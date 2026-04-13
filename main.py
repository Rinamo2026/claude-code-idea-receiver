"""idea-receiver — FastAPI エントリーポイント"""
import asyncio
import ipaddress
import json
import logging
import secrets
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, Response, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
import models
import projects as projects_mod
import watcher as watcher_mod
import auth

LOG_FILE = config.BASE_DIR / "idea-receiver.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# --- WebSocket ブロードキャスト ---
connected_clients: list[WebSocket] = []


async def broadcast(message: dict):
    data = json.dumps(message, ensure_ascii=False)
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_text(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_clients.remove(ws)


# --- ライフサイクル ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    await models.init_db()
    config.IDEAS_DIR.mkdir(parents=True, exist_ok=True)
    config.DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("idea-receiver started on port %d", config.SERVER_PORT)
    watcher_mod.set_broadcast(broadcast)
    loop = asyncio.get_event_loop()
    observer = watcher_mod.start_watcher(loop)
    # スタートアップスキャン: 未処理のアイディアを検出して処理
    await _startup_scan(loop)
    yield
    observer.stop()
    observer.join(timeout=5)
    await models.close_db()
    logger.info("idea-receiver stopped")


async def _startup_scan(loop):
    """再起動時に未処理のアイディアを検出して逐次パイプラインに投入"""
    try:
        ideas = await models.get_all_ideas(limit=0)  # 全件取得
        pending = [i for i in ideas if i["status"] == "received"]
        if pending:
            logger.info("Startup scan: %d pending ideas found", len(pending))
            for idea in pending:
                idea_file = config.IDEAS_DIR / f"{idea['id']}.json"
                if idea_file.exists():
                    try:
                        await watcher_mod.process_idea(idea_file)
                    except Exception as e:
                        logger.warning("Startup scan: failed to process %s: %s", idea["id"], e)
    except Exception as e:
        logger.warning("Startup scan failed: %s", e)


app = FastAPI(title="Idea Receiver", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(config.BASE_DIR / "static")), name="static")


# --- Reverse proxy helpers ---
def _get_prefix(request: Request) -> str:
    """X-Forwarded-Prefix ヘッダーからベースパスを取得"""
    return request.headers.get("x-forwarded-prefix", "").rstrip("/")


def _serve_html(filename: str, request: Request) -> HTMLResponse:
    """HTMLを配信。プロキシ経由時は <base> タグと JS 変数を注入"""
    html_path = config.BASE_DIR / "static" / filename
    html = html_path.read_text(encoding="utf-8")
    prefix = _get_prefix(request)
    if prefix:
        inject = (
            f'<base href="{prefix}/">\n'
            f'<script>window.__BASE_PATH="{prefix}"</script>'
        )
        html = html.replace("</head>", f"{inject}\n</head>", 1)
        # プロキシ経由時のナビゲーションリンク修正
        html = html.replace('href="/dashboard"', 'href="/portal/"')
        html = html.replace('href="/ideas"', 'href="/ideas/"')
    return HTMLResponse(html)


# --- Schemas ---
class IdeaSubmit(BaseModel):
    text: str


class DraftSave(BaseModel):
    id: str | None = None
    content: str


class AuthCredential(BaseModel):
    credential: dict


# --- 認証ミドルウェア ---
def _is_local_request(request: Request) -> bool:
    """ローカルホストからのリクエストかどうか判定（IPv4-mapped IPv6対応）"""
    client = request.client
    if not client:
        return False
    host = client.host
    try:
        addr = ipaddress.ip_address(host)
        return addr.is_loopback
    except ValueError:
        return host == "localhost"


async def require_auth(request: Request):
    """認証チェック。クレデンシャルが0件 or ローカル直接リクエストなら認証不要"""
    # プロキシ経由（Tailscale Funnel等）でない直接のローカル接続のみバイパス
    forwarded = request.headers.get("x-forwarded-for")
    if _is_local_request(request) and not forwarded:
        return
    cred_count = await models.get_credential_count()
    if cred_count == 0:
        return
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(401, "Not authenticated")
    session = await models.get_session(session_id)
    if not session:
        raise HTTPException(401, "Session expired")


# --- Health ---
@app.get("/health")
async def health():
    return {"status": "ok"}


# --- Root (prefix-aware) ---
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    prefix = _get_prefix(request)
    if prefix == "/ideas":
        return _serve_html("index.html", request)
    elif prefix == "/portal":
        return _serve_html("dashboard.html", request)
    return _serve_html("portal.html", request)


# --- SPA ---
@app.get("/ideas", response_class=HTMLResponse)
async def ideas(request: Request):
    return _serve_html("index.html", request)


# --- Auth API ---
@app.get("/api/auth/status")
async def auth_status(request: Request):
    cred_count = await models.get_credential_count()
    session_id = request.cookies.get("session_id")
    logged_in = False
    if session_id:
        session = await models.get_session(session_id)
        logged_in = session is not None
    # ローカル直接接続（プロキシ経由でない）なら認証不要
    forwarded = request.headers.get("x-forwarded-for")
    local_bypass = _is_local_request(request) and not forwarded
    return {"credential_count": cred_count, "logged_in": logged_in, "local_bypass": local_bypass}


@app.post("/api/auth/register/options")
async def register_options(request: Request):
    # 初回セットアップ後はログイン済みユーザーのみ登録可能
    cred_count = await models.get_credential_count()
    if cred_count > 0:
        session_id = request.cookies.get("session_id")
        if not session_id or not await models.get_session(session_id):
            raise HTTPException(403, "Registration requires authentication after initial setup")
    options_json = await auth.get_registration_options()
    return JSONResponse(content=json.loads(options_json))


@app.post("/api/auth/register/verify")
async def register_verify(body: AuthCredential, request: Request):
    # 初回セットアップ後はログイン済みユーザーのみ登録可能
    cred_count = await models.get_credential_count()
    if cred_count > 0:
        session_id = request.cookies.get("session_id")
        if not session_id or not await models.get_session(session_id):
            raise HTTPException(403, "Registration requires authentication after initial setup")
    try:
        await auth.verify_registration(body.credential)
    except Exception as e:
        raise HTTPException(400, str(e))

    # 登録直後はセッションを手動発行
    session_id = secrets.token_urlsafe(32)
    expires = (datetime.now(tz=timezone.utc) + timedelta(seconds=config.SESSION_MAX_AGE)).strftime("%Y-%m-%d %H:%M:%S")
    await models.insert_session(session_id, "owner", expires)

    response = JSONResponse({"status": "registered"})
    response.set_cookie(
        "session_id", session_id,
        max_age=config.SESSION_MAX_AGE,
        httponly=True, secure=True, samesite="strict",
    )
    return response


@app.post("/api/auth/login/options")
async def login_options():
    options_json = await auth.get_authentication_options()
    return JSONResponse(content=json.loads(options_json))


@app.post("/api/auth/login/verify")
async def login_verify(body: AuthCredential):
    try:
        session_id = await auth.verify_authentication(body.credential)
    except Exception as e:
        raise HTTPException(401, str(e))

    response = JSONResponse({"status": "authenticated"})
    response.set_cookie(
        "session_id", session_id,
        max_age=config.SESSION_MAX_AGE,
        httponly=True, secure=True, samesite="strict",
    )
    return response


@app.post("/api/auth/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        await models.delete_session(session_id)
    response = JSONResponse({"status": "logged_out"})
    response.delete_cookie("session_id")
    return response


# --- Ideas API ---
@app.post("/api/ideas")
async def submit_idea(body: IdeaSubmit, _=Depends(require_auth)):
    idea_id = uuid.uuid4().hex[:12]
    idea = await models.insert_idea(idea_id, body.text)
    idea_file = config.IDEAS_DIR / f"{idea_id}.json"
    idea_file.write_text(
        json.dumps({"id": idea_id, "text": body.text}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    await broadcast({"type": "idea_submitted", "idea": idea})
    logger.info("Idea submitted: %s", idea_id)
    return idea


@app.get("/api/ideas")
async def list_ideas(_=Depends(require_auth)):
    return await models.get_all_ideas()


@app.get("/api/ideas/{idea_id}")
async def get_idea(idea_id: str, _=Depends(require_auth)):
    idea = await models.get_idea(idea_id)
    if not idea:
        raise HTTPException(404, "Idea not found")
    return idea


@app.post("/api/ideas/{idea_id}/retry")
async def retry_idea(idea_id: str, _=Depends(require_auth)):
    idea = await models.get_idea(idea_id)
    if not idea:
        raise HTTPException(404, "Idea not found")
    if idea["status"] != "failed":
        raise HTTPException(400, "Idea is not in failed state")
    await models.update_idea(idea_id, status="received", error=None)
    idea_file = config.IDEAS_DIR / f"{idea_id}.json"
    idea_file.write_text(
        json.dumps({"id": idea_id, "text": idea["raw_text"]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"status": "retrying", "id": idea_id}


@app.post("/api/ideas/{idea_id}/submit")
async def submit_existing_idea(idea_id: str, _=Depends(require_auth)):
    """停止中のアイディアのパイプラインを手動トリガー"""
    idea = await models.get_idea(idea_id)
    if not idea:
        raise HTTPException(404, "Idea not found")
    # 処理中・完了済みは再投入不可
    if idea["status"] in ("classifying", "creating", "launching"):
        raise HTTPException(409, f"Idea is currently being processed (status: {idea['status']})")
    if idea["status"] == "active":
        raise HTTPException(400, "Idea already completed")
    # received / failed / その他の停止状態 → パイプライン再トリガー
    await models.update_idea(idea_id, status="received", error=None)
    idea_file = config.IDEAS_DIR / f"{idea_id}.json"
    idea_file.write_text(
        json.dumps({"id": idea_id, "text": idea["raw_text"]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"status": "submitted", "id": idea_id}


# --- Drafts API ---
@app.post("/api/drafts")
async def save_draft(body: DraftSave, _=Depends(require_auth)):
    draft_id = body.id or uuid.uuid4().hex[:12]
    await models.upsert_draft(draft_id, body.content)
    return {"id": draft_id, "content": body.content}


@app.get("/api/drafts")
async def list_drafts(_=Depends(require_auth)):
    return await models.get_all_drafts()


@app.get("/api/drafts/{draft_id}")
async def get_draft(draft_id: str, _=Depends(require_auth)):
    draft = await models.get_draft(draft_id)
    if not draft:
        raise HTTPException(404, "Draft not found")
    return draft


@app.delete("/api/drafts/{draft_id}")
async def delete_draft(draft_id: str, _=Depends(require_auth)):
    await models.delete_draft(draft_id)
    return {"status": "deleted"}


# --- WebSocket ---
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    # 認証チェック（クレデンシャル未登録時はスキップ）
    cred_count = await models.get_credential_count()
    if cred_count > 0:
        session_id = ws.cookies.get("session_id")
        if not session_id or not await models.get_session(session_id):
            await ws.close(code=4001)
            return
    await ws.accept()
    connected_clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        if ws in connected_clients:
            connected_clients.remove(ws)


# --- Dashboard ---
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return _serve_html("dashboard.html", request)


# --- Projects API ---
@app.get("/api/projects")
async def list_projects(_=Depends(require_auth)):
    ideas = await models.get_all_ideas(limit=200)
    return [projects_mod.enrich_idea(idea) for idea in ideas]


# --- カテゴリ一覧 ---
@app.get("/api/categories")
async def list_categories(_=Depends(require_auth)):
    import re
    categories = []
    for d in sorted(config.DEV_ROOT.iterdir()):
        if d.is_dir() and re.match(r"^\d{2}_", d.name):
            subs = [s.name for s in d.iterdir() if s.is_dir() and not s.name.startswith(".")]
            categories.append({
                "id": d.name[:2],
                "name": d.name[3:],
                "path": str(d),
                "projects": subs,
            })
    return categories


# --- 起動 ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
    )
