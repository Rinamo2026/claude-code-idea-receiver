"""プロジェクト作成 — init-project.sh (bundled or custom) + ドメイン別handoff.md 生成"""
import asyncio
import functools
import json
import logging
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

import config
from classifier import ClassificationResult
from domains import (
    get_domain,
    format_team_roster_markdown,
    format_phases_markdown,
    format_innovation_gate_markdown,
    format_genealogy_framework_markdown,
    build_team_roster,
    DOMAINS,
)

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))

_jinja_env = Environment(
    loader=FileSystemLoader(str(config.BASE_DIR / "templates")),
    keep_trailing_newline=True,
)


def _next_project_number(category_dir: Path) -> str:
    """カテゴリ内の次のプロジェクト番号を計算(3桁ゼロパディング)"""
    max_num = 0
    if category_dir.exists():
        for d in category_dir.iterdir():
            if d.is_dir():
                m = re.match(r"^(\d{2,3})", d.name)
                if m:
                    max_num = max(max_num, int(m.group(1)))
    return f"{max_num + 1:03d}"


def _build_claude_md(classification: ClassificationResult, cat_dir: Path, idea_id: str) -> str:
    """CLAUDE.mdを生成 — メタデータ + handoff.mdポインタのみ。内容はhandoff.mdに一本化。"""
    domain = get_domain(classification.domain) or get_domain("business")

    return (
        f"# {classification.project_name_jp}\n\n"
        f"- カテゴリ: `{cat_dir.name}`\n"
        f"- ドメイン: {domain.domain_name} ({domain.domain_id})\n"
        f"- チーム: {domain.team_name}\n"
        f"- アイディアID: `{idea_id}`\n\n"
        f"## セッション開始手順\n"
        f"**まず `handoff.md` を読み込んでください。**\n"
        f"アイディア原文、チーム編成、フェーズ定義、Innovation Gate、方針の全てが記載されています。\n"
    )


def _sanitize_name(name: str) -> str:
    """パストラバーサル防止: 英数字・アンダースコア・ハイフンのみ許可"""
    sanitized = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
    # 連続アンダースコアを圧縮し、先頭末尾のアンダースコアを除去
    sanitized = re.sub(r'_+', '_', sanitized).strip('_')
    return sanitized or "unnamed"


def _validate_path_within(path: Path, base: Path) -> Path:
    """パスがbase配下に収まることを検証"""
    resolved = path.resolve()
    base_resolved = base.resolve()
    if not resolved.is_relative_to(base_resolved):
        raise RuntimeError(f"Path traversal detected: {path} escapes {base}")
    return resolved


async def create_project(
    classification: ClassificationResult,
    idea_id: str,
    raw_text: str,
) -> str:
    """プロジェクトを作成し、handoff.md を配置。プロジェクトパスを返す。"""

    # 入力サニタイズ（パストラバーサル防止）
    classification.project_name = _sanitize_name(classification.project_name)
    # LLMが既存プロジェクト名を参考に番号プレフィクス付きの名前を返すことがあるため除去
    classification.project_name = re.sub(r'^\d+_', '', classification.project_name) or "unnamed"
    if not re.match(r'^\d{2}$', classification.category_id):
        logger.warning("Invalid category_id '%s', sanitizing", classification.category_id)
        classification.category_id = re.sub(r'[^0-9]', '', classification.category_id)[:2].zfill(2)

    # カテゴリディレクトリ
    if classification.is_new_category:
        new_name = classification.raw_json.get("new_category_name")
        if not new_name:
            new_name = f"{classification.category_id}_{classification.category_name}"
        # カテゴリ名もサニタイズ
        new_name = _sanitize_name(new_name)
        cat_dir = config.DEV_ROOT / new_name
        _validate_path_within(cat_dir, config.DEV_ROOT)
        cat_dir.mkdir(parents=True, exist_ok=True)
        logger.info("New category created: %s", cat_dir)
    else:
        # 既存カテゴリを探す
        cat_dir = None
        for d in config.DEV_ROOT.iterdir():
            if d.is_dir() and d.name.startswith(f"{classification.category_id}_"):
                cat_dir = d
                break
        if not cat_dir:
            raise RuntimeError(f"Category not found: {classification.category_id}")

    # プロジェクト番号 + 名前
    proj_num = _next_project_number(cat_dir)
    proj_dir_name = f"{proj_num}_{classification.project_name}"
    proj_path = cat_dir / proj_dir_name
    _validate_path_within(proj_path, config.DEV_ROOT)

    # プロジェクトディレクトリ初期化
    # Resolve init script: user-provided > bundled template
    init_script = config.INIT_PROJECT_SCRIPT
    if not init_script:
        bundled = config.BASE_DIR / "templates" / "init-project.sh"
        if bundled.exists():
            init_script = str(bundled)

    loop = asyncio.get_event_loop()
    if init_script:
        result = await loop.run_in_executor(
            None,
            functools.partial(
                subprocess.run,
                [config.GIT_BASH, init_script, str(proj_path), "--git"],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            ),
        )
        if result.returncode != 0:
            raise RuntimeError(f"init-project.sh failed (rc={result.returncode}): stdout={result.stdout.strip()} stderr={result.stderr.strip()}")
        logger.info("Project created via %s: %s",
                     "custom script" if config.INIT_PROJECT_SCRIPT else "bundled template",
                     result.stdout.strip())
    else:
        # Minimal fallback: no bash available or template missing
        proj_path.mkdir(parents=True, exist_ok=True)
        (proj_path / "memory").mkdir(exist_ok=True)
        await loop.run_in_executor(
            None,
            functools.partial(
                subprocess.run,
                ["git", "init", str(proj_path)],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            ),
        )
        logger.info("Project created (minimal fallback): %s", proj_path)

    # ドメイン情報取得
    domain = get_domain(classification.domain) or get_domain("business")

    # CLAUDE.md をカスタマイズ（ドメイン対応版）
    claude_md = proj_path / "CLAUDE.md"
    claude_md.write_text(
        _build_claude_md(classification, cat_dir, idea_id),
        encoding="utf-8",
    )

    # handoff.md を生成（ドメイン対応版）
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")
    template = _jinja_env.get_template("handoff.md.j2")
    handoff_content = template.render(
        project_name_jp=classification.project_name_jp,
        created_at=now,
        category_path=cat_dir.name,
        domain_id=domain.domain_id,
        domain_name=domain.domain_name,
        idea_id=idea_id,
        confidence=classification.confidence,
        raw_text=raw_text,
        core_summary=classification.core_summary,
        interpretations=classification.interpretations,
        classification_reason=classification.classification_reason,
        related_projects=classification.related_projects,
        is_new_category=classification.is_new_category,
        ambiguous_points=classification.ambiguous_points,
        genealogy_framework=format_genealogy_framework_markdown(domain),
        team_roster=format_team_roster_markdown(domain),
        phases=format_phases_markdown(domain),
        innovation_gate=format_innovation_gate_markdown(domain),
        gate_level=domain.innovation_gate.gate_level,
        extra_specialist_reasons=classification.extra_specialists,
    )
    handoff_path = proj_path / "handoff.md"
    handoff_path.write_text(handoff_content, encoding="utf-8")
    logger.info("handoff.md generated (domain=%s, team=%s): %s",
                domain.domain_id, domain.team_name, handoff_path)

    # /start コマンドを handoff.md 対応に上書き（ドメイン対応版）
    start_cmd = proj_path / ".claude" / "commands" / "start.md"
    start_cmd.parent.mkdir(parents=True, exist_ok=True)
    start_cmd.write_text(
        "handoff.md を読み込み、内容を把握してください。\n"
        "次に memory/index.md があれば読み込んでください。\n"
        "その後、handoff.md の「推奨アクション」に従って作業を開始してください。\n\n"
        "## 必須手順\n"
        "1. 未確定論点があればユーザーに確認する\n"
        "2. チームメンバーをサブエージェントとして並列起動し、Phase 1 の調査を開始する\n"
        "3. Phase 2 完了後、Innovation Gate を必ず実施する\n"
        "4. ゲート通過後のみ Phase 3 以降に進む\n"
        "5. 結果は全て memory/ に保存する\n",
        encoding="utf-8",
    )

    # settings.local.json を広い権限で上書き（自動実行用）
    settings_path = proj_path / ".claude" / "settings.local.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps({
        "permissions": {
            "allow": [
                "Bash(*)",
                "Read(*)",
                "Write(*)",
                "Edit(*)",
                "Glob(*)",
                "Grep(*)",
                "WebFetch(*)",
                "WebSearch(*)",
            ],
            "deny": [
                "Bash(rm *)",
                "Bash(rm -*)",
                "Bash(rmdir *)",
                "Bash(del *)",
                "Bash(rd *)",
                "Bash(mv /*)",
                "Bash(truncate *)",
                "Bash(dd *)",
                "Bash(shred *)",
                "Bash(git clean*)",
                "Bash(git reset --hard*)",
                "Bash(git push --force*)",
                "Bash(git push -f*)",
                "Bash(git branch -D*)",
                "Bash(git checkout -- *)",
                "Bash(git restore *)",
            ]
        }
    }, indent=2), encoding="utf-8")

    # 原文も保存
    (proj_path / "idea_raw.txt").write_text(raw_text, encoding="utf-8")

    return str(proj_path)
