"""idea-receiver 設定"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("IDEA_RECEIVER_PORT", "8702"))

IDEAS_DIR = Path(os.getenv("IDEAS_DIR", str(BASE_DIR / "data" / "ideas")))
DRAFTS_DIR = Path(os.getenv("DRAFTS_DIR", str(BASE_DIR / "data" / "drafts")))
DB_PATH = str(BASE_DIR / "idea_receiver.db")

DEV_ROOT = Path(os.getenv("DEV_ROOT", str(BASE_DIR / "projects")))
INIT_PROJECT_SCRIPT = os.getenv("INIT_PROJECT_SCRIPT", "")
GIT_BASH = os.getenv("GIT_BASH", "bash")
CLAUDE_CLI = "claude"

# WebAuthn — 必ず環境変数で設定してください (See README: Setup)
RP_ID = os.getenv("RP_ID", "localhost")
RP_NAME = "Idea Receiver"
ORIGIN = os.getenv("ORIGIN", "http://localhost:8702")

# セッション
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7日

# 分類
CATEGORIES_CACHE_SEC = 300
