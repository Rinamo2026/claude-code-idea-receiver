"""プロジェクト情報の収集 — ideas + ファイルシステムメタデータ"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def enrich_idea(idea: dict) -> dict:
    """ideaレコードにファイルシステム情報を付加して返す"""
    result = {**idea}

    # classification_json からプロジェクト名等を抽出
    cls_json = idea.get("classification_json")
    if cls_json:
        try:
            cls = json.loads(cls_json)
            result["project_name"] = cls.get("project_name", "")
            result["project_name_jp"] = cls.get("project_name_jp", "")
            result["category"] = cls.get("category_name", "")
            result["confidence"] = cls.get("confidence")
            result["core_summary"] = cls.get("core_summary", "")
        except (json.JSONDecodeError, TypeError):
            pass

    # デフォルト値
    result.setdefault("project_name", "")
    result.setdefault("project_name_jp", "")
    result.setdefault("category", "")
    result.setdefault("confidence", None)
    result.setdefault("core_summary", "")

    # ファイルシステムから進捗情報を取得
    project_path = idea.get("project_path")
    result["has_handoff"] = False
    result["has_market_research"] = False
    result["has_git"] = False
    result["memory_count"] = 0

    if project_path:
        p = Path(project_path)
        if p.exists():
            result["has_handoff"] = (p / "handoff.md").exists()
            result["has_market_research"] = (p / "memory" / "market_research.md").exists()
            result["has_git"] = (p / ".git").exists()
            mem_dir = p / "memory"
            if mem_dir.exists():
                result["memory_count"] = sum(
                    1 for f in mem_dir.iterdir()
                    if f.is_file() and f.suffix == ".md" and f.name != "index.md"
                )

    return result
