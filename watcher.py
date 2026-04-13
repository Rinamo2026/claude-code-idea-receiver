"""watchdog ファイル監視 — 新規アイディア検知 → パイプライン実行"""
import asyncio
import json
import logging
import time
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import config
import models
from classifier import classify_idea
from project_creator import create_project
from session_launcher import launch_session

logger = logging.getLogger(__name__)

_broadcast = None
_processing: set[str] = set()  # 処理中のファイルを追跡（プロセス内ガード）


def set_broadcast(fn):
    global _broadcast
    _broadcast = fn


async def _notify(idea_id: str, status: str, **extra):
    """WebSocket + DB更新"""
    await models.update_idea(idea_id, status=status, **extra)
    if _broadcast:
        await _broadcast({"type": "idea_status", "idea_id": idea_id, "status": status, **extra})


async def process_idea(idea_path: Path):
    """分類 → プロジェクト作成 → セッション起動のパイプライン"""
    idea_id = idea_path.stem

    # ガード1: プロセス内メモリ（同一プロセスの重複イベント排除）
    if idea_id in _processing:
        return
    _processing.add(idea_id)

    try:
        # idea_idのバリデーション（パストラバーサル防止）
        import re
        if not re.match(r'^[a-zA-Z0-9]+$', idea_id):
            logger.warning("Invalid idea_id: %s", idea_id)
            return

        # JSONを読む（ファイル書き込み完了を待つため短いリトライ）
        for _retry in range(3):
            try:
                data = json.loads(idea_path.read_text(encoding="utf-8"))
                break
            except (json.JSONDecodeError, OSError):
                if _retry == 2:
                    raise
                await asyncio.sleep(0.5)

        raw_text = data.get("text", "")
        if not raw_text:
            logger.warning("Empty idea text: %s", idea_id)
            return

        # 既にproject_pathがあれば重複作成を防止
        idea = await models.get_idea(idea_id)
        if idea and idea.get("project_path"):
            existing = Path(idea["project_path"])
            if existing.exists():
                # 既存プロジェクトの再起動はホワイトリスト方式
                # （watchdog modified イベントによる全件再起動を防止）
                status = idea.get("status", "")
                if status not in ("received", "failed"):
                    logger.debug(
                        "Idea %s already %s at %s, skipping re-launch",
                        idea_id, status, existing,
                    )
                    return
                logger.info("Idea %s already has project at %s, re-launching (status=%s)", idea_id, existing, status)
                handoff_path = str(existing / "handoff.md")
                await _notify(idea_id, "launching")
                await launch_session(str(existing), handoff_path)
                await _notify(idea_id, "active")
                logger.info("[%s] Session re-launched for existing project.", idea_id)
                return

        # ガード2: アトミックDB claim（複数プロセスの排他制御）
        # UPDATE ... WHERE status='received' で1プロセスだけが claim 成功する
        if not await models.claim_idea(idea_id):
            logger.info("Idea %s already claimed by another process, skipping", idea_id)
            return

        # --- Step 1: 分類 ---
        logger.info("[%s] Classifying...", idea_id)
        if _broadcast:
            await _broadcast({"type": "idea_status", "idea_id": idea_id, "status": "classifying"})

        classification = await classify_idea(raw_text)
        logger.info(
            "[%s] Classified → %s_%s/%s (confidence: %.2f)",
            idea_id, classification.category_id, classification.category_name,
            classification.project_name, classification.confidence,
        )

        await _notify(
            idea_id, "classifying",
            classification_json=json.dumps(classification.raw_json, ensure_ascii=False),
        )

        # --- Step 2: プロジェクト作成 ---
        logger.info("[%s] Creating project...", idea_id)
        await _notify(idea_id, "creating")

        project_path = await create_project(classification, idea_id, raw_text)
        logger.info("[%s] Project created: %s", idea_id, project_path)

        await _notify(idea_id, "creating", project_path=project_path)

        # --- Step 3: セッション起動 ---
        logger.info("[%s] Launching session...", idea_id)
        await _notify(idea_id, "launching")

        handoff_path = str(Path(project_path) / "handoff.md")
        await launch_session(project_path, handoff_path, classification.project_name_jp)

        # --- 完了 ---
        await _notify(idea_id, "active")
        logger.info("[%s] Pipeline complete. Session active.", idea_id)

    except Exception as e:
        logger.error("[%s] Pipeline failed: %s", idea_id, e, exc_info=True)
        try:
            await _notify(idea_id, "failed", error=str(e))
        except Exception:
            pass
    finally:
        _processing.discard(idea_id)


class IdeaFileHandler(FileSystemEventHandler):
    """data/ideas/ に新規JSONファイルが作成されたら処理開始"""

    DEBOUNCE_SEC = 2.0  # 同一ファイルの連続イベントを抑制

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self._last_seen: dict[str, float] = {}

    def _handle(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix != ".json":
            return

        # デバウンス: 同一ファイルの連続イベントを抑制
        now = time.monotonic()
        last = self._last_seen.get(path.name, 0.0)
        if now - last < self.DEBOUNCE_SEC:
            return
        self._last_seen[path.name] = now

        logger.info("Idea file detected (%s): %s", event.event_type, path.name)
        asyncio.run_coroutine_threadsafe(process_idea(path), self._loop)

    def on_created(self, event):
        self._handle(event)

    def on_modified(self, event):
        self._handle(event)


def start_watcher(loop: asyncio.AbstractEventLoop) -> Observer:
    """watchdog を別スレッドで起動"""
    handler = IdeaFileHandler(loop)
    observer = Observer()
    observer.schedule(handler, str(config.IDEAS_DIR), recursive=False)
    observer.daemon = True
    observer.start()
    logger.info("Watcher started: monitoring %s", config.IDEAS_DIR)
    return observer
