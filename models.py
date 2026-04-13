"""DB モデル (aiosqlite)"""
import asyncio

import aiosqlite
import config

_db: aiosqlite.Connection | None = None
_db_lock = asyncio.Lock()


async def get_db() -> aiosqlite.Connection:
    global _db
    async with _db_lock:
        if _db is None:
            _db = await aiosqlite.connect(config.DB_PATH)
            _db.row_factory = aiosqlite.Row
    return _db


async def init_db():
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS ideas (
            id TEXT PRIMARY KEY,
            raw_text TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'received',
            category TEXT,
            project_path TEXT,
            classification_json TEXT,
            error TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS credentials (
            credential_id BLOB PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id),
            public_key BLOB NOT NULL,
            sign_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id),
            expires_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS drafts (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)
    await db.commit()


async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None


# --- Ideas ---

async def insert_idea(idea_id: str, raw_text: str) -> dict:
    db = await get_db()
    await db.execute(
        "INSERT INTO ideas (id, raw_text) VALUES (?, ?)",
        (idea_id, raw_text),
    )
    await db.commit()
    return {"id": idea_id, "raw_text": raw_text, "status": "received"}


_IDEA_ALLOWED_COLUMNS = {"status", "category", "project_path", "classification_json", "error"}


async def update_idea(idea_id: str, **kwargs):
    db = await get_db()
    for k in kwargs:
        if k not in _IDEA_ALLOWED_COLUMNS:
            raise ValueError(f"Invalid column for ideas table: {k}")
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values())
    vals.append(idea_id)
    await db.execute(
        f"UPDATE ideas SET {sets}, updated_at = datetime('now') WHERE id = ?",
        vals,
    )
    await db.commit()


async def claim_idea(idea_id: str) -> bool:
    """Atomically claim an idea for processing.

    Uses UPDATE ... WHERE status='received' so only one process can claim.
    Returns True if this call successfully claimed the idea.
    """
    db = await get_db()
    cursor = await db.execute(
        "UPDATE ideas SET status = 'classifying', updated_at = datetime('now') "
        "WHERE id = ? AND status = 'received'",
        (idea_id,),
    )
    await db.commit()
    return cursor.rowcount > 0


async def get_idea(idea_id: str) -> dict | None:
    db = await get_db()
    cur = await db.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
    row = await cur.fetchone()
    return dict(row) if row else None


async def get_all_ideas(limit: int = 50) -> list[dict]:
    db = await get_db()
    if limit <= 0:
        cur = await db.execute("SELECT * FROM ideas ORDER BY created_at DESC")
    else:
        cur = await db.execute(
            "SELECT * FROM ideas ORDER BY created_at DESC LIMIT ?", (limit,)
        )
    return [dict(r) for r in await cur.fetchall()]


# --- Drafts ---

async def upsert_draft(draft_id: str, content: str):
    db = await get_db()
    await db.execute(
        """INSERT INTO drafts (id, content, updated_at)
           VALUES (?, ?, datetime('now'))
           ON CONFLICT(id) DO UPDATE SET content=excluded.content, updated_at=datetime('now')""",
        (draft_id, content),
    )
    await db.commit()


async def get_draft(draft_id: str) -> dict | None:
    db = await get_db()
    cur = await db.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,))
    row = await cur.fetchone()
    return dict(row) if row else None


async def get_all_drafts() -> list[dict]:
    db = await get_db()
    cur = await db.execute("SELECT * FROM drafts ORDER BY updated_at DESC")
    return [dict(r) for r in await cur.fetchall()]


async def delete_draft(draft_id: str):
    db = await get_db()
    await db.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
    await db.commit()


# --- Auth ---

async def get_credential_count() -> int:
    db = await get_db()
    cur = await db.execute("SELECT COUNT(*) FROM credentials")
    row = await cur.fetchone()
    return row[0]


async def insert_user(user_id: str, name: str):
    db = await get_db()
    await db.execute(
        "INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)",
        (user_id, name),
    )
    await db.commit()


async def insert_credential(credential_id: bytes, user_id: str, public_key: bytes, sign_count: int):
    db = await get_db()
    await db.execute(
        "INSERT INTO credentials (credential_id, user_id, public_key, sign_count) VALUES (?, ?, ?, ?)",
        (credential_id, user_id, public_key, sign_count),
    )
    await db.commit()


async def get_credential(credential_id: bytes) -> dict | None:
    db = await get_db()
    cur = await db.execute("SELECT * FROM credentials WHERE credential_id = ?", (credential_id,))
    row = await cur.fetchone()
    return dict(row) if row else None


async def get_user_credentials(user_id: str) -> list[dict]:
    db = await get_db()
    cur = await db.execute("SELECT * FROM credentials WHERE user_id = ?", (user_id,))
    return [dict(r) for r in await cur.fetchall()]


async def update_sign_count(credential_id: bytes, sign_count: int):
    db = await get_db()
    await db.execute(
        "UPDATE credentials SET sign_count = ? WHERE credential_id = ?",
        (sign_count, credential_id),
    )
    await db.commit()


async def insert_session(session_id: str, user_id: str, expires_at: str):
    db = await get_db()
    await db.execute(
        "INSERT INTO sessions (session_id, user_id, expires_at) VALUES (?, ?, ?)",
        (session_id, user_id, expires_at),
    )
    await db.commit()


async def get_session(session_id: str) -> dict | None:
    db = await get_db()
    cur = await db.execute(
        "SELECT * FROM sessions WHERE session_id = ? AND expires_at > datetime('now')",
        (session_id,),
    )
    row = await cur.fetchone()
    return dict(row) if row else None


async def delete_session(session_id: str):
    db = await get_db()
    await db.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    await db.commit()
