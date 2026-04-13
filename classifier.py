"""claude -p による分類エンジン"""
import asyncio
import functools
import ipaddress
import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import httpx

import config
from domains import get_domain_summary, get_all_domain_ids

logger = logging.getLogger(__name__)

_categories_cache: list[dict] | None = None
_categories_cache_time: float = 0


@dataclass
class ClassificationResult:
    category_id: str
    category_name: str
    project_name: str
    project_name_jp: str
    is_new_category: bool
    classification_reason: str
    core_summary: str
    interpretations: list[str]
    related_projects: list[dict]
    ambiguous_points: list[str]
    confidence: float
    domain: str = "business"           # ドメイン種別 (domains.py の domain_id)
    extra_specialists: list[str] = field(default_factory=list)  # 追加すべき専門家の理由
    raw_json: dict = field(default_factory=dict)


async def scan_categories() -> list[dict]:
    """DEV_ROOT 配下のカテゴリ一覧を走査(キャッシュ付き)"""
    global _categories_cache, _categories_cache_time

    now = time.time()
    if _categories_cache and (now - _categories_cache_time) < config.CATEGORIES_CACHE_SEC:
        return _categories_cache

    categories = []
    dev_root = config.DEV_ROOT
    for d in sorted(dev_root.iterdir()):
        if d.is_dir() and re.match(r"^\d{2}_", d.name):
            subs = []
            for s in sorted(d.iterdir()):
                if s.is_dir() and not s.name.startswith("."):
                    # CLAUDE.md があればプロジェクト概要も読む
                    claude_md = s / "CLAUDE.md"
                    desc = ""
                    if claude_md.exists():
                        try:
                            first_line = claude_md.read_text(encoding="utf-8").split("\n")[0]
                            desc = first_line.lstrip("# ").strip()
                        except Exception:
                            pass
                    subs.append({"name": s.name, "description": desc})
            categories.append({
                "id": d.name[:2],
                "name": d.name[3:],
                "path": str(d),
                "projects": subs,
            })

    _categories_cache = categories
    _categories_cache_time = now
    return categories


def _build_classification_prompt(idea_text: str, categories: list[dict]) -> str:
    cats_json = json.dumps(categories, ensure_ascii=False, indent=2)
    domain_summary = get_domain_summary()
    return f"""あなたはプロジェクト分類アシスタントです。
以下のアイディアを、既存カテゴリのいずれかに分類し、最適なドメインを判定してください。

## 既存カテゴリ
{cats_json}

## ドメイン種別（プロジェクトの性質に最も近いものを1つ選択）
{domain_summary}

## アイディア
{idea_text}

## 出力形式 (JSONのみ、説明文不要、```json```で囲まない)
{{
  "category_id": "01",
  "category_name": "MyCategory",
  "is_new_category": false,
  "new_category_name": null,
  "project_name": "short_english_name",
  "project_name_jp": "日本語プロジェクト名",
  "classification_reason": "分類理由",
  "core_summary": "アイディアの核を1-2文で",
  "interpretations": ["解釈候補1", "解釈候補2", "解釈候補3"],
  "related_projects": [
    {{"path": "01_MyCategory/003_example_project", "reason": "類似点の説明"}}
  ],
  "ambiguous_points": ["不明点1", "不明点2"],
  "confidence": 0.85,
  "domain": "development",
  "extra_specialists": ["UIを持つアプリケーションのためUXデザインアドバイザーが必要", "LLM活用を含むためLLMスペシャリストが必要"]
}}

## ルール
- 既存カテゴリに当てはまるなら is_new_category: false
- どのカテゴリにも当てはまらない場合のみ is_new_category: true にし、new_category_name に "XX_名前" 形式で提案
- 新カテゴリの番号は既存の最大番号 + 1 (現在の最大: {max(c['id'] for c in categories)})
- confidence が 0.5 未満なら ambiguous_points に判断根拠を詳しく記載
- project_name は英数字とアンダースコアのみ。番号プレフィクスは不要（自動付与されるため "024_xxx" ではなく "xxx" のみ）
- 関連プロジェクトは既存のプロジェクト一覧から類似するものを探す
- domain はドメイン種別一覧から最も適切なものを1つ選ぶ
- extra_specialists: アイディアの内容に応じて追加すべき専門家がいれば、その理由を記載する（空配列でも可）"""


def _is_safe_url(url: str) -> bool:
    """SSRF防止: ループバック・プライベートIPへのアクセスを拒否"""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        addr = ipaddress.ip_address(hostname)
        return addr.is_global
    except ValueError:
        # ホスト名（非IP）→ 既知の内部ホスト名を拒否
        hostname = urlparse(url).hostname or ""
        return hostname not in ("localhost", "host.docker.internal")


async def _prefetch_urls(text: str) -> str:
    """テキスト中のURLコンテンツを事前取得し補足テキストを付加する"""
    url_pattern = re.compile(r'https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+')
    urls = url_pattern.findall(text)
    if not urls:
        return text

    supplements = []
    headers = {"User-Agent": "idea-receiver/1.0"}
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        for url in urls:
            if not _is_safe_url(url):
                logger.warning("SSRF blocked: %s", url)
                continue
            try:
                # X/Twitter → fxtwitter API
                m = re.match(r'https?://(x\.com|twitter\.com)/(.+)', url)
                if m:
                    api_url = f"https://api.fxtwitter.com/{m.group(2)}"
                    # クエリパラメータを除去
                    api_url = api_url.split('?')[0]
                    resp = await client.get(api_url, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        tweet = data.get("tweet", {})
                        tweet_text = tweet.get("text", "")
                        author = tweet.get("author", {}).get("name", "")
                        if tweet_text:
                            supplements.append(
                                f"[URL内容: {url}]\n投稿者: {author}\n内容: {tweet_text}"
                            )
                            continue

                # 一般URL: HTMLからタイトル・description抽出
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    html = resp.text[:10000]
                    parts = []
                    title_m = re.search(
                        r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE
                    )
                    desc_m = re.search(
                        r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\']'
                        r'[^>]+content=["\']([^"\']+)',
                        html, re.IGNORECASE,
                    )
                    if title_m:
                        parts.append(f"タイトル: {title_m.group(1).strip()}")
                    if desc_m:
                        parts.append(f"概要: {desc_m.group(1).strip()}")
                    if parts:
                        supplements.append(
                            f"[URL内容: {url}]\n" + "\n".join(parts)
                        )
            except Exception as e:
                logger.debug("URL prefetch failed for %s: %s", url, e)

    if supplements:
        return text + "\n\n--- 以下はURLから自動取得した補足情報 ---\n" + "\n\n".join(supplements)
    return text


async def classify_idea(idea_text: str) -> ClassificationResult:
    """claude -p でアイディアを分類"""
    # URL含有時はコンテンツを事前取得して補足
    enriched_text = await _prefetch_urls(idea_text)
    if enriched_text != idea_text:
        logger.info("URL content prefetched, enriched text length: %d → %d",
                     len(idea_text), len(enriched_text))

    categories = await scan_categories()
    prompt = _build_classification_prompt(enriched_text, categories)

    for attempt in range(3):
        try:
            # CLAUDECODE環境変数をunsetしてネスト制限を回避、git-bashパスを確保
            env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
            env.setdefault("CLAUDE_CODE_GIT_BASH_PATH", config.GIT_BASH)

            # Windows asyncioはsubprocessをサポートしないため、スレッドプールで実行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                functools.partial(
                    subprocess.run,
                    [config.CLAUDE_CLI, "-p", prompt, "--output-format", "text"],
                    capture_output=True,
                    cwd=str(config.DEV_ROOT),
                    env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                ),
            )

            if result.returncode != 0:
                logger.warning("claude -p failed (attempt %d): %s", attempt + 1, result.stderr.decode())
                continue

            raw = result.stdout.decode("utf-8").strip()

            # JSON部分を抽出: 最初の { から最後の } までを切り出す
            first_brace = raw.find('{')
            last_brace = raw.rfind('}')
            json_candidate = raw[first_brace:last_brace + 1] if first_brace >= 0 and last_brace > first_brace else None
            if not json_candidate:
                logger.warning("No JSON found in output (attempt %d): %s", attempt + 1, raw[:200])
                continue

            data = json.loads(json_candidate)

            # ドメイン値の検証
            domain_val = data.get("domain", "business")
            valid_domains = get_all_domain_ids()
            if domain_val not in valid_domains:
                logger.warning("Unknown domain '%s', falling back to 'business'", domain_val)
                domain_val = "business"

            # extra_specialistsの型チェック
            extra_specs = data.get("extra_specialists", [])
            if not isinstance(extra_specs, list):
                extra_specs = []
            extra_specs = [str(s) for s in extra_specs]

            return ClassificationResult(
                category_id=data.get("category_id", "01"),
                category_name=data.get("category_name", ""),
                project_name=data.get("project_name", "unnamed"),
                project_name_jp=data.get("project_name_jp", ""),
                is_new_category=data.get("is_new_category", False),
                classification_reason=data.get("classification_reason", ""),
                core_summary=data.get("core_summary", ""),
                interpretations=data.get("interpretations", []),
                related_projects=data.get("related_projects", []),
                ambiguous_points=data.get("ambiguous_points", []),
                confidence=data.get("confidence", 0.5),
                domain=domain_val,
                extra_specialists=extra_specs,
                raw_json=data,
            )

        except json.JSONDecodeError as e:
            logger.warning("JSON parse error (attempt %d): %s", attempt + 1, e)
            continue
        except Exception as e:
            logger.error("Classification error (attempt %d): %s", attempt + 1, e)
            if attempt == 2:
                raise

    raise RuntimeError("Classification failed after 3 attempts")
