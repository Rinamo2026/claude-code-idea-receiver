"""ドメイン定義 — 分野別チーム構成・フェーズ・イノベーションゲート"""

from dataclasses import dataclass, field


@dataclass
class TeamMember:
    role_id: str          # 一意識別子
    role_name: str        # 日本語役職名
    perspective: str      # このメンバーの視点・専門
    prompt_directive: str  # サブエージェントに渡す指示の核


# ── 共通メンバー (全ドメイン必須) ────────────────────────────────
CORE_MEMBERS = [
    TeamMember(
        role_id="genealogist",
        role_name="系譜研究員（Genealogist）",
        perspective="要素分解・歴史的系譜・発展の文脈・フロンティア検出",
        prompt_directive=(
            "【系譜分析】以下の5ステップを実行し、結果を memory/genealogy.md に保存せよ。\n"
            "深度設定（要素数・MCP使用数・クロスドメイン有無）は Phase 0 のタスク記述に従うこと。\n\n"
            "### Step 1: 要素分解（Element Decomposition）\n"
            "アイディアを構成する核心的な要素・概念・技術・手法を全て洗い出せ。\n"
            "各要素に「これは何の分野に属するか」のタグを付けよ。\n\n"
            "### Step 2: 系譜調査（Lineage Tracing）\n"
            "分解した各要素について以下を調査せよ:\n"
            "- 起源: この概念/技術はいつ、どこで、誰によって生まれたか\n"
            "- 発展の系譜: 主要なマイルストーン（転換点となった出来事、論文、製品、作品）\n"
            "- 現在の最前線: 今この要素はどこまで進んでいるか（State of the Art）\n"
            "- 進化の方向性: 次の発展として予測されるもの\n"
            "- 停滞・失敗した分岐: 試みられたが行き詰まったアプローチとその理由\n\n"
            "### Step 3: フロンティアマップ（Frontier Mapping）\n"
            "各要素の系譜から、以下を特定せよ:\n"
            "- 未開拓領域: まだ誰も試みていない組み合わせや応用\n"
            "- 停滞ブレイクスルー候補: 行き詰まっているが新技術で突破可能な領域\n"
            "- 本アイディアがどの未解決課題に取り組むか\n\n"
            "### Step 4: クロスドメイン注入（Cross-Domain Injection）\n"
            "※ Phase 0 のタスク記述で「クロスドメイン: なし」の場合はこのステップをスキップせよ。\n"
            "各要素について、別の分野で類似の問題がどう解決されたかを調査せよ:\n"
            "- 類似構造を持つ他分野の手法（アナロジー）を3つ以上\n"
            "- その分野での成功パターンが本プロジェクトに転用可能か評価\n"
            "- 異分野の融合で生まれた歴史的な成功事例を参照\n\n"
            "### Step 5: 発展ナラティブ（Development Narrative）\n"
            "上記の全分析を統合し、各要素について1段落で構築せよ:\n"
            "「[要素X]は[起源]から[発展]を経て[現在の最前線]に至った。\n"
            " しかし[未開拓領域/未解決課題]は手付かずのままである。\n"
            " 本プロジェクトは[アプローチ]によりこの課題に取り組む。」\n\n"
            "## 出力形式（memory/genealogy.md）\n"
            "## [要素名]\n"
            "- 起源: ...\n"
            "- SOTA: ...\n"
            "- 未解決課題: ...\n"
            "- 本PJの位置づけ: ...\n"
            "- クロスドメイン知見: ...（Step 4 実行時のみ）\n"
        ),
    ),
    TeamMember(
        role_id="prompt_architect",
        role_name="AIプロンプトアーキテクト",
        perspective="LLMの特性を最大限引き出す構造設計",
        prompt_directive=(
            "このプロジェクトの指示書・プロンプト構造を最適化せよ。\n"
            "Chain-of-Thought、Few-shot、Tree-of-Thought等の思考フレームワークから最適なものを選定し、\n"
            "AIが最高品質の出力を生成できる構造を設計すること。\n"
            "特に系譜研究員の分析結果を踏まえ、各要素の発展段階に応じた最適な思考モードを提案すること。"
        ),
    ),
    TeamMember(
        role_id="innovation_catalyst",
        role_name="イノベーション・カタリスト",
        perspective="未知の発見・異分野融合・セレンディピティ誘発",
        prompt_directive=(
            "系譜研究員のフロンティアマップを土台として、以下を実施せよ:\n"
            "1. 系譜の「空白地帯」に対して、異分野からの技術移転候補を3つ以上提案\n"
            "2. 逆張り仮説（系譜の常識を覆すアプローチ）を2つ以上提示\n"
            "3. 隣接可能性（Adjacent Possible）の探索 — 系譜上の複数要素が合流する未踏の交差点\n"
            "4. 系譜の「停滞分岐」を復活させる新技術・新手法の提案\n"
            "5. 10年後のビジョンからのバックキャスト — この分野の系譜は次にどう進むべきか\n"
            "6. 異分野の発展パターンとの構造的類似性（isomorphism）を探索\n"
            "結果を memory/innovation_analysis.md に保存せよ。"
        ),
    ),
    TeamMember(
        role_id="critical_reviewer",
        role_name="批判的レビュアー（Devil's Advocate）",
        perspective="盲点の発見・前提への疑義・失敗モード分析",
        prompt_directive=(
            "系譜分析・イノベーション提案に対して徹底的な批判的分析を実施せよ:\n"
            "1. 系譜分析の盲点 — 見落とされている重要な発展の分岐はないか\n"
            "2. 暗黙の前提を全て洗い出し、各前提が崩れた場合の影響を評価\n"
            "3. Pre-mortem分析 — 1年後にこのプロジェクトが失敗したと仮定し、最も可能性の高い失敗原因を5つ挙げよ\n"
            "4. 系譜上の「成功バイアス」 — 過去の成功パターンに過度に依存していないか\n"
            "5. クロスドメイン注入のリスク — 他分野の手法が本当にこの文脈で機能するか\n"
            "6. 致命的欠陥候補 — プロジェクトを殺しうる要因のランク付け\n"
            "結果を memory/critical_review.md に保存せよ。"
        ),
    ),
    TeamMember(
        role_id="knowledge_integrator",
        role_name="ナレッジ・インテグレーター",
        perspective="既存資産との接続・知識統合・重複排除",
        prompt_directive=(
            "以下を調査・統合せよ:\n"
            "1. DEV_ROOT 配下の既存プロジェクトとの関連性・シナジーを分析\n"
            "2. 既存のmemory/ナレッジベースから活用可能な知見を抽出\n"
            "3. 重複する取り組みがないか確認し、統合の可否を判断\n"
            "4. 他プロジェクトの失敗教訓で本プロジェクトに適用可能なものを列挙\n"
            "5. 系譜分析で発見された知見を他プロジェクトに逆輸入できるか評価"
        ),
    ),
]


# ── ドメイン定義 ────────────────────────────────────────────────

@dataclass
class DomainPhase:
    name: str
    description: str
    tasks: list[str]
    output: str  # 成果物ファイル名


@dataclass
class InnovationGate:
    """Phase移行前の必須チェックポイント"""
    gate_name: str
    criteria: list[str]
    minimum_score: str  # "全項目クリア" or "3/5以上" etc.
    gate_level: str = "strict"  # "strict" / "moderate" / "practical"


@dataclass
class GenealogyDepth:
    """系譜調査の深度設定 — ドメイン別にトークン効率を制御"""
    max_elements: int = 5                  # 要素分解の上限
    max_sources_per_element: int = 2       # 要素ごとのMCP検索ソース数上限
    include_cross_domain: bool = True      # Step 4 クロスドメイン注入を含むか


@dataclass
class DomainConfig:
    domain_id: str
    domain_name: str
    team_name: str         # プロジェクトチーム名
    team_motto: str        # チームモットー
    description: str
    specialist_members: list[TeamMember]  # ドメイン固有メンバー
    phases: list[DomainPhase]
    innovation_gate: InnovationGate
    extra_member_triggers: list[dict]  # 条件付き追加メンバー
    genealogy_depth: GenealogyDepth = field(default_factory=GenealogyDepth)


# ── 全ドメイン共通 Phase 0: 系譜分析 ──────────────────────────────
# このフェーズは全ドメインのPhase 1の前に自動挿入される
GENEALOGY_PHASE = DomainPhase(
    name="Phase 0: 系譜分析（Genealogy Analysis）",
    description="発展の文脈の中に位置づける — 全ドメイン共通・最重要フェーズ",
    tasks=[
        "【実行方法】系譜研究員（genealogist）をサブエージェントとして起動し、以下のタスクを委譲する。"
        " prompt_directive はチームロスターの genealogist を参照。深度設定は上記の「深度設定」欄に従うこと。",
        "【Step 1: 要素分解】アイディアを構成する核心要素を分解し、各要素の所属分野をタグ付けする",
        "【Step 2: 系譜調査】各要素の起源・発展マイルストーン・SOTA・停滞分岐を調査する",
        "【Step 3: フロンティアマップ】各要素の未開拓領域・本PJが取り組む未解決課題を特定する",
        "【Step 4: クロスドメイン注入】（深度設定で有効な場合）他分野の類似解決策・技術移転候補を調査する",
        "【Step 5: 発展ナラティブ】各要素について「起源→発展→現在→本PJの取り組み」の1段落を構築する",
        "【保存】全結果を memory/genealogy.md に保存してから Phase 1 へ進む",
    ],
    output="memory/genealogy.md",
)


DOMAINS: dict[str, DomainConfig] = {}


def _register(config: DomainConfig):
    DOMAINS[config.domain_id] = config
    return config


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 事業・ビジネス
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_register(DomainConfig(
    domain_id="business",
    domain_name="事業・ビジネス",
    team_name="Venture Lab",
    team_motto="市場を創る、価値を届ける",
    description="新規事業、ビジネスモデル、サービス企画、マーケティング",
    specialist_members=[
        TeamMember(
            role_id="market_strategist",
            role_name="市場戦略アナリスト",
            perspective="市場構造・競争環境・参入戦略",
            prompt_directive=(
                "市場調査を徹底実施せよ:\n"
                "1. TAM/SAM/SOM分析\n"
                "2. Porter's Five Forces分析\n"
                "3. 競合マッピング（直接/間接/潜在競合）\n"
                "4. Blue Ocean戦略キャンバス\n"
                "5. 参入タイミング分析（First-mover vs Fast-follower）"
            ),
        ),
        TeamMember(
            role_id="biz_model_designer",
            role_name="ビジネスモデル設計士",
            perspective="収益構造・スケーラビリティ・持続性",
            prompt_directive=(
                "ビジネスモデルを設計せよ:\n"
                "1. Business Model Canvas完成\n"
                "2. 収益モデル候補を3パターン以上提示\n"
                "3. ユニットエコノミクス試算\n"
                "4. スケーラビリティ評価\n"
                "5. モート（参入障壁）構築戦略"
            ),
        ),
    ],
    phases=[
        DomainPhase(
            name="Phase 1: 市場偵察 + 系譜統合",
            description="市場の最先端に立ち、系譜の中での位置を確定する",
            tasks=[
                "競合・先行事例の網羅的調査（成功/失敗の両方）",
                "最新技術・手法のサーベイ（直近6ヶ月のブレイクスルー）",
                "市場規模・成長率・トレンド分析",
                "ユーザーのペインポイント・Jobs-to-be-done分析",
                "規制・法的環境の調査",
                "【系譜統合】Phase 0の系譜分析を市場文脈と統合 — この事業は業界発展の系譜のどこに位置づけられるか",
                "【系譜統合】過去の類似事業モデルの盛衰パターンから学ぶべき教訓を抽出",
            ],
            output="memory/market_research.md",
        ),
        DomainPhase(
            name="Phase 2: 差別化戦略",
            description="競合が到達できない領域を特定する",
            tasks=[
                "ホワイトスペース（競合不在領域）の特定",
                "Value Proposition Canvas作成",
                "差別化の持続可能性評価",
                "ポジショニングマップ作成",
            ],
            output="memory/differentiation_strategy.md",
        ),
        DomainPhase(
            name="Phase 3: ビジネス設計",
            description="収益化と持続性を設計する",
            tasks=[
                "Business Model Canvas完成",
                "収益モデル比較検討",
                "Go-to-Market戦略策定",
                "KPI設計",
            ],
            output="memory/business_model.md",
        ),
        DomainPhase(
            name="Phase 4: MVP・実行計画",
            description="最小実行案を具体化する",
            tasks=[
                "MVP機能セット定義",
                "技術スタック選定",
                "実装ロードマップ作成",
                "リスク軽減策の具体化",
            ],
            output="memory/mvp_plan.md",
        ),
    ],
    innovation_gate=InnovationGate(
        gate_name="Venture Gate",
        criteria=[
            "系譜的位置づけ: この事業が業界の発展系譜のどこに位置し、何を前進させるかが明確か",
            "新規性: 系譜分析で特定されたフロンティア（未開拓領域）に踏み込んでいるか",
            "差別化: 競合が容易に模倣できない、系譜上の独自ポジションを確保しているか",
            "クロスドメイン活用: 他分野からの知見が有効に組み込まれているか",
            "市場機会: 未充足ニーズまたは未開拓セグメントが実データで裏付けられているか",
            "タイミング: 系譜上の技術成熟度と市場準備度が今このタイミングを支持しているか",
        ],
        minimum_score="全6項目のうち5項目以上クリア",
        gate_level="strict",
    ),
    extra_member_triggers=[
        {
            "condition": "法規制・コンプライアンスに関連する内容",
            "member": TeamMember(
                role_id="regulatory_advisor",
                role_name="規制・コンプライアンスアドバイザー",
                perspective="法規制、プライバシー、知的財産",
                prompt_directive="関連する法規制、コンプライアンス要件、知的財産リスクを調査し報告せよ。",
            ),
        },
        {
            "condition": "ハードウェアや物理的プロダクトを含む",
            "member": TeamMember(
                role_id="hardware_advisor",
                role_name="ハードウェアアドバイザー",
                perspective="製造、サプライチェーン、物理設計",
                prompt_directive="製造可能性、サプライチェーン、コスト構造を分析せよ。",
            ),
        },
    ],
    genealogy_depth=GenealogyDepth(max_elements=4, max_sources_per_element=2, include_cross_domain=True),
))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 研究・学術
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_register(DomainConfig(
    domain_id="research",
    domain_name="研究・学術",
    team_name="Deep Dive",
    team_motto="未知を既知に変える",
    description="学術研究、実験設計、論文サーベイ、仮説検証",
    specialist_members=[
        TeamMember(
            role_id="literature_surveyor",
            role_name="文献サーベイヤー",
            perspective="先行研究の網羅的調査・系統的レビュー",
            prompt_directive=(
                "系統的文献レビューを実施せよ:\n"
                "1. 関連キーワード・MeSH/学術用語の網羅的リスト作成\n"
                "2. 主要論文・レビュー論文の特定と要約\n"
                "3. 研究のギャップ（未解決問題）の特定\n"
                "4. 方法論の比較と最新手法の整理\n"
                "5. 引用ネットワークからの重要論文の特定"
            ),
        ),
        TeamMember(
            role_id="hypothesis_architect",
            role_name="仮説設計士",
            perspective="仮説構築・実験設計・検証計画",
            prompt_directive=(
                "研究仮説と検証計画を設計せよ:\n"
                "1. 主仮説と対立仮説の明確な定式化\n"
                "2. 検証可能な予測の導出\n"
                "3. 実験/調査デザインの提案（対照群、サンプルサイズ等）\n"
                "4. 想定される反論と対応策\n"
                "5. 再現性を確保するためのプロトコル設計"
            ),
        ),
    ],
    phases=[
        DomainPhase(
            name="Phase 1: 文献偵察 + 系譜統合",
            description="研究領域の全体像と発展の系譜を統合的に把握する",
            tasks=[
                "キーワード・用語の整理とサーチクエリ設計",
                "主要論文・レビュー論文のサーベイ",
                "研究ギャップ（未解決問題）の特定",
                "最新手法・最新成果の整理",
                "関連する研究グループ・機関の把握",
                "【系譜統合】Phase 0の各要素系譜を学術文脈に接続 — この研究は学問の発展史のどの分岐点に立つか",
                "【系譜統合】パラダイムシフトの歴史を整理し、次のシフトの候補を特定",
            ],
            output="memory/literature_survey.md",
        ),
        DomainPhase(
            name="Phase 2: 仮説構築",
            description="検証可能な仮説を構造化する",
            tasks=[
                "リサーチクエスチョンの精緻化",
                "仮説ツリーの構築（主仮説→副仮説）",
                "各仮説の検証方法の概略設計",
                "必要なデータ/リソースの特定",
            ],
            output="memory/hypothesis.md",
        ),
        DomainPhase(
            name="Phase 3: 実験設計",
            description="再現性のある検証プロトコルを設計する",
            tasks=[
                "実験/調査デザインの詳細化",
                "データ収集・分析パイプラインの設計",
                "ツール・環境のセットアップ計画",
                "タイムライン策定",
            ],
            output="memory/experiment_design.md",
        ),
        DomainPhase(
            name="Phase 4: プロトタイプ実験",
            description="小規模で仮説の方向性を検証する",
            tasks=[
                "最小限のパイロット実験/PoC実施",
                "予備データの分析",
                "仮説の修正・精緻化",
                "本実験への改善点整理",
            ],
            output="memory/pilot_results.md",
        ),
    ],
    innovation_gate=InnovationGate(
        gate_name="Discovery Gate",
        criteria=[
            "系譜的位置づけ: この研究が分野の発展系譜のどこに位置し、何を前進させるかが明確か",
            "新規性: 系譜分析で特定された研究ギャップ・未開拓領域に踏み込んでいるか",
            "独自性: 既存アプローチと異なる方法論・視点があり、それが別分野からの知見を含むか",
            "学術的意義: 分野の知識体系に新たな分岐点（milestone）を作る可能性があるか",
            "検証可能性: 反証可能な形で仮説が定式化されているか",
            "再現性: 第三者が追試可能な設計になっているか",
        ],
        minimum_score="全6項目のうち5項目以上クリア",
        gate_level="strict",
    ),
    extra_member_triggers=[
        {
            "condition": "統計分析や機械学習を含む研究",
            "member": TeamMember(
                role_id="stats_advisor",
                role_name="統計・ML手法アドバイザー",
                perspective="統計設計、機械学習パイプライン",
                prompt_directive="統計手法の妥当性、検定力分析、ML手法の選定を評価せよ。",
            ),
        },
        {
            "condition": "人を対象とする研究（調査・実験）",
            "member": TeamMember(
                role_id="ethics_advisor",
                role_name="研究倫理アドバイザー",
                perspective="研究倫理、インフォームドコンセント",
                prompt_directive="倫理的配慮、IRB要件、データ保護について助言せよ。",
            ),
        },
    ],
    genealogy_depth=GenealogyDepth(max_elements=5, max_sources_per_element=3, include_cross_domain=True),
))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. ソフトウェア開発
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_register(DomainConfig(
    domain_id="development",
    domain_name="ソフトウェア開発",
    team_name="Forge",
    team_motto="堅牢に、美しく、速く",
    description="アプリ開発、ツール開発、ライブラリ、システム構築",
    specialist_members=[
        TeamMember(
            role_id="tech_scout",
            role_name="技術スカウト",
            perspective="最新技術調査・技術選定・アーキテクチャ",
            prompt_directive=(
                "技術調査を実施せよ:\n"
                "1. 要件に最適な技術スタック候補を3セット以上提示\n"
                "2. 各候補のトレードオフ分析（性能、学習コスト、エコシステム、将来性）\n"
                "3. 類似OSSプロジェクトの調査と差別化ポイント\n"
                "4. パフォーマンス・スケーラビリティの予測\n"
                "5. セキュリティ上の考慮事項"
            ),
        ),
        TeamMember(
            role_id="arch_designer",
            role_name="アーキテクチャ設計士",
            perspective="システム設計・拡張性・保守性",
            prompt_directive=(
                "アーキテクチャを設計せよ:\n"
                "1. システム全体のアーキテクチャ図（コンポーネント、データフロー）\n"
                "2. 主要な設計判断とそのトレードオフ\n"
                "3. 拡張ポイントの設計（プラグイン機構等）\n"
                "4. エラーハンドリング戦略\n"
                "5. テスト戦略（ユニット、統合、E2E）"
            ),
        ),
    ],
    phases=[
        DomainPhase(
            name="Phase 1: 技術偵察 + 系譜統合",
            description="技術の最前線と発展系譜を統合的に把握する",
            tasks=[
                "類似OSS/ツールの網羅的調査",
                "最新技術スタック・フレームワークのサーベイ",
                "ベンチマーク・性能比較データの収集",
                "セキュリティ上のベストプラクティス調査",
                "ライセンス・依存関係の確認",
                "【系譜統合】Phase 0の各要素系譜を技術発展の文脈に接続 — この技術は何の進化の延長線上にあるか",
                "【系譜統合】技術の世代交代パターン（置換・共存・融合）を分析し、本プロジェクトの位置づけを決定",
            ],
            output="memory/tech_survey.md",
        ),
        DomainPhase(
            name="Phase 2: アーキテクチャ設計",
            description="拡張性と保守性を両立する設計",
            tasks=[
                "要件の構造化（機能要件/非機能要件）",
                "アーキテクチャ候補の比較検討",
                "コンポーネント分割とインターフェース定義",
                "データモデル設計",
                "技術スタックの最終選定と根拠",
            ],
            output="memory/architecture.md",
        ),
        DomainPhase(
            name="Phase 3: プロトタイプ",
            description="核となる機能を動くコードで実証する",
            tasks=[
                "コアとなるモジュールの実装",
                "PoC（概念実証）の作成",
                "基本的なテストの整備",
                "パフォーマンス計測",
            ],
            output="memory/prototype_notes.md",
        ),
        DomainPhase(
            name="Phase 4: MVP実装",
            description="最小限の完成品を作る",
            tasks=[
                "フル機能実装",
                "テストスイート整備",
                "ドキュメント作成",
                "CI/CD設計",
            ],
            output="memory/mvp_progress.md",
        ),
    ],
    innovation_gate=InnovationGate(
        gate_name="Forge Gate",
        criteria=[
            "系譜的位置づけ: この技術が発展系譜のどこに位置し、何を前進させるかが明確か",
            "技術的新規性: 系譜分析で特定されたフロンティアに踏み込んでいるか",
            "差別化: 類似OSSの系譜的限界を超えるアプローチがあるか",
            "クロスドメイン活用: 他分野の設計パターン・解決策が有効に組み込まれているか",
            "設計品質: 拡張性・保守性に優れた設計になっているか",
            "実用性: 実際のユースケースで既存の代替手段より優れているか",
        ],
        minimum_score="全6項目のうち5項目以上クリア",
        gate_level="strict",
    ),
    extra_member_triggers=[
        {
            "condition": "UIを持つアプリケーション",
            "member": TeamMember(
                role_id="ux_designer",
                role_name="UXデザインアドバイザー",
                perspective="ユーザー体験設計、アクセシビリティ",
                prompt_directive="ユーザーフロー、UIパターン、アクセシビリティを設計せよ。",
            ),
        },
        {
            "condition": "分散システムやマイクロサービスを含む",
            "member": TeamMember(
                role_id="distributed_advisor",
                role_name="分散システムアドバイザー",
                perspective="分散合意、障害耐性、一貫性",
                prompt_directive="分散アーキテクチャの設計、障害モード、一貫性モデルを評価せよ。",
            ),
        },
    ],
    genealogy_depth=GenealogyDepth(max_elements=4, max_sources_per_element=2, include_cross_domain=True),
))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 創作・アート
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_register(DomainConfig(
    domain_id="creative",
    domain_name="創作・アート",
    team_name="Atelier",
    team_motto="想像を超える表現を",
    description="作品制作、物語、デザイン、音楽、映像、世界観構築",
    specialist_members=[
        TeamMember(
            role_id="concept_artist",
            role_name="コンセプトアーティスト",
            perspective="世界観構築・ビジュアルコンセプト・美的方向性",
            prompt_directive=(
                "コンセプト設計を実施せよ:\n"
                "1. コアコンセプト（テーマ、メッセージ、情動）の定義\n"
                "2. ムードボード的な参照作品・影響源の収集\n"
                "3. 世界観/スタイルの骨格設計\n"
                "4. ビジュアル方向性の提案（3パターン以上）\n"
                "5. 受け手の体験設計（どんな感情・思考を誘発したいか）"
            ),
        ),
        TeamMember(
            role_id="narrative_designer",
            role_name="ナラティブデザイナー",
            perspective="物語構造・テーマ・受け手の体験設計",
            prompt_directive=(
                "ナラティブ設計を実施せよ:\n"
                "1. テーマとメタファーの構造化\n"
                "2. 物語構造の選定（三幕構成、英雄の旅、非線形等）\n"
                "3. キャラクター/要素のアーキタイプ分析\n"
                "4. 感情曲線（Emotional Arc）の設計\n"
                "5. 受け手の解釈の余白設計"
            ),
        ),
    ],
    phases=[
        DomainPhase(
            name="Phase 1: インスピレーション収集 + 系譜統合",
            description="表現の最前線と歴史的系譜を統合的に把握する",
            tasks=[
                "同ジャンル/隣接ジャンルの優れた作品のサーベイ",
                "最新の表現技法・ツール・メディアの調査",
                "ターゲットオーディエンスの嗜好・トレンド分析",
                "【系譜統合】Phase 0の各要素系譜を表現史に接続 — このジャンルの発展の系譜を時系列で整理",
                "【系譜統合】各時代の転換点（パラダイムシフト作品）を特定し、次の転換を予測",
                "【系譜統合】異分野の表現進化パターンから着想を得る（例: 建築→絵画、音楽→文学のクロス影響）",
                "異分野からの着想源の探索 — 系譜上の交差点で生まれた歴史的傑作を参照",
            ],
            output="memory/inspiration.md",
        ),
        DomainPhase(
            name="Phase 2: コンセプト設計",
            description="作品の核となるコンセプトを結晶化する",
            tasks=[
                "コアコンセプトの定義（テーマ、メッセージ、情動）",
                "世界観/スタイルガイドの骨格",
                "表現手法の選定と根拠",
                "受け手の体験設計",
            ],
            output="memory/concept.md",
        ),
        DomainPhase(
            name="Phase 3: プロトタイプ制作",
            description="最小限の形で核を実現する",
            tasks=[
                "コアシーン/コア要素の制作",
                "フィードバック収集計画",
                "技術的課題の洗い出し",
                "イテレーション計画",
            ],
            output="memory/prototype.md",
        ),
        DomainPhase(
            name="Phase 4: 制作・完成",
            description="完成品のクオリティで仕上げる",
            tasks=[
                "本制作の実行",
                "品質チェック・ブラッシュアップ",
                "公開/展示計画",
                "振り返り・次回作への知見",
            ],
            output="memory/production.md",
        ),
    ],
    innovation_gate=InnovationGate(
        gate_name="Atelier Gate",
        criteria=[
            "表現の核: 伝えたいこと・表現したいことが明確に設計されているか",
            "独自性: 他にない視点・表現・アプローチがあれば加点（必須ではない）",
            "技法の適切性: 表現意図に対して技法・メディアの選択が適切か",
            "深度: 表面的でなく、多層的な解釈を許す深さがあるか",
            "共鳴性: ターゲットの感情・思考に響く要素が設計されているか",
            "完成度: 作品として成立する水準に到達しているか",
        ],
        minimum_score="全6項目のうち4項目以上クリア",
        gate_level="moderate",
    ),
    extra_member_triggers=[
        {
            "condition": "AI生成（画像/音声/映像）を含む創作",
            "member": TeamMember(
                role_id="ai_art_advisor",
                role_name="AI生成アートアドバイザー",
                perspective="生成AI技法、プロンプトエンジニアリング、ワークフロー",
                prompt_directive="最適な生成AIモデル/ツールの選定、プロンプト戦略、品質向上手法を提案せよ。",
            ),
        },
        {
            "condition": "インタラクティブ作品（ゲーム、体験型等）",
            "member": TeamMember(
                role_id="interaction_designer",
                role_name="インタラクションデザイナー",
                perspective="プレイヤー体験、ゲームメカニクス",
                prompt_directive="インタラクション設計、フィードバックループ、プレイヤー心理を設計せよ。",
            ),
        },
    ],
    genealogy_depth=GenealogyDepth(max_elements=3, max_sources_per_element=1, include_cross_domain=False),
))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 情報収集・分析
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_register(DomainConfig(
    domain_id="intelligence",
    domain_name="情報収集・分析",
    team_name="Insight",
    team_motto="データから洞察へ、洞察から行動へ",
    description="調査、データ分析、OSINT、トレンド把握、レポート作成",
    specialist_members=[
        TeamMember(
            role_id="osint_analyst",
            role_name="OSINT/調査アナリスト",
            perspective="公開情報の収集・検証・構造化",
            prompt_directive=(
                "情報収集を実施せよ:\n"
                "1. 情報源の特定と信頼性評価\n"
                "2. 複数ソースからのクロスバリデーション\n"
                "3. タイムライン構築\n"
                "4. ステークホルダーマッピング\n"
                "5. 情報の鮮度・バイアス評価"
            ),
        ),
        TeamMember(
            role_id="data_synthesizer",
            role_name="データ統合アナリスト",
            perspective="データの統合・可視化・洞察抽出",
            prompt_directive=(
                "データ統合と分析を実施せよ:\n"
                "1. 収集データの構造化・正規化\n"
                "2. パターンと異常値の特定\n"
                "3. トレンド分析と将来予測\n"
                "4. エグゼクティブサマリーの作成\n"
                "5. アクショナブルな提言の導出"
            ),
        ),
    ],
    phases=[
        DomainPhase(
            name="Phase 1: スコーピング + 系譜統合",
            description="調査範囲を定義し、対象領域の系譜的文脈を把握する",
            tasks=[
                "調査目的の明確化とRQ（Research Question）設定",
                "情報源の特定とアクセス方法の整理",
                "収集するデータの種類・粒度の定義",
                "バイアス・限界の事前把握",
                "成果物のフォーマット合意",
                "【系譜統合】Phase 0の系譜分析を調査文脈に接続 — 過去の類似調査の方法論進化を把握",
                "【系譜統合】情報収集手法の系譜（従来手法→現代手法→次世代手法）を整理し最適な手法を選定",
            ],
            output="memory/scope.md",
        ),
        DomainPhase(
            name="Phase 2: 多角収集",
            description="複数の情報源から網羅的に収集する",
            tasks=[
                "一次情報源からの収集",
                "二次情報源からの補完",
                "クロスバリデーション",
                "タイムライン・関係図の構築",
                "情報の信頼度スコアリング",
            ],
            output="memory/raw_intelligence.md",
        ),
        DomainPhase(
            name="Phase 3: 統合分析",
            description="データを洞察に変換する",
            tasks=[
                "パターン認識と仮説構築",
                "矛盾点の解消または明示",
                "So-What分析（だからどうなのか）",
                "シナリオ分析（楽観/基本/悲観）",
                "アクショナブルインサイトの抽出",
            ],
            output="memory/analysis.md",
        ),
        DomainPhase(
            name="Phase 4: レポーティング",
            description="意思決定に使えるレポートを作成する",
            tasks=[
                "エグゼクティブサマリー作成",
                "詳細レポート構成",
                "可視化・図表作成",
                "提言と次ステップの提示",
            ],
            output="memory/report.md",
        ),
    ],
    innovation_gate=InnovationGate(
        gate_name="Insight Gate",
        criteria=[
            "分析の深さ: 対象領域の背景・文脈が十分に把握されているか",
            "網羅性: 主要な情報源が漏れなくカバーされているか",
            "洞察の質: 表面的な情報整理を超えた独自の分析視点があるか",
            "検証性: 結論の根拠が追跡可能か",
            "適時性: 情報の鮮度が目的に対して十分か",
            "実用性: 具体的な行動につながる提言があるか",
        ],
        minimum_score="全6項目のうち5項目以上クリア",
        gate_level="moderate",
    ),
    extra_member_triggers=[
        {
            "condition": "数値データの統計分析を含む",
            "member": TeamMember(
                role_id="quant_analyst",
                role_name="定量分析アドバイザー",
                perspective="統計分析、データ可視化",
                prompt_directive="統計的手法の選定、有意性検定、可視化方法を設計せよ。",
            ),
        },
    ],
    genealogy_depth=GenealogyDepth(max_elements=5, max_sources_per_element=2, include_cross_domain=True),
))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. インフラ・環境整備
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_register(DomainConfig(
    domain_id="infrastructure",
    domain_name="インフラ・環境整備",
    team_name="Foundation",
    team_motto="見えない基盤が全てを支える",
    description="DevOps、CI/CD、サーバー、ネットワーク、開発環境構築",
    specialist_members=[
        TeamMember(
            role_id="infra_architect",
            role_name="インフラアーキテクト",
            perspective="可用性、スケーラビリティ、コスト最適化",
            prompt_directive=(
                "インフラ設計を実施せよ:\n"
                "1. 現状の環境分析と課題特定\n"
                "2. アーキテクチャ候補の比較（オンプレ/クラウド/ハイブリッド）\n"
                "3. 可用性・障害耐性の設計\n"
                "4. コスト試算と最適化戦略\n"
                "5. セキュリティ要件の整理"
            ),
        ),
        TeamMember(
            role_id="automation_engineer",
            role_name="自動化エンジニア",
            perspective="IaC、CI/CD、運用自動化",
            prompt_directive=(
                "自動化戦略を設計せよ:\n"
                "1. 自動化対象の優先順位付け\n"
                "2. IaCツール選定（Terraform/Ansible/etc）\n"
                "3. CI/CDパイプライン設計\n"
                "4. モニタリング・アラート設計\n"
                "5. 障害時の自動復旧設計"
            ),
        ),
    ],
    phases=[
        DomainPhase(
            name="Phase 1: 現状分析 + 系譜統合",
            description="現在の環境を棚卸しし、インフラ技術の発展系譜の中で課題を特定する",
            tasks=[
                "既存環境のインベントリ作成",
                "ボトルネック・障害点の特定",
                "最新のベストプラクティス調査",
                "セキュリティ監査",
                "コスト分析",
                "【系譜統合】Phase 0の系譜分析をインフラ技術史に接続 — 現環境は技術世代のどこに位置するか",
                "【系譜統合】インフラパラダイムの変遷（物理→仮想→コンテナ→サーバーレス→...）における次の移行先を評価",
            ],
            output="memory/current_state.md",
        ),
        DomainPhase(
            name="Phase 2: 設計",
            description="あるべき姿を設計する",
            tasks=[
                "To-Beアーキテクチャの設計",
                "移行計画の策定",
                "リスク分析と軽減策",
                "テスト計画",
            ],
            output="memory/design.md",
        ),
        DomainPhase(
            name="Phase 3: 構築",
            description="設計を実装する",
            tasks=[
                "段階的な構築・移行",
                "テスト実施",
                "ドキュメント整備",
                "運用手順書作成",
            ],
            output="memory/implementation.md",
        ),
        DomainPhase(
            name="Phase 4: 運用安定化",
            description="安定稼働を確認し運用に移行する",
            tasks=[
                "モニタリング設定と閾値調整",
                "負荷テスト",
                "障害訓練",
                "引き渡し・ナレッジ移管",
            ],
            output="memory/operations.md",
        ),
    ],
    innovation_gate=InnovationGate(
        gate_name="Foundation Gate",
        criteria=[
            "技術選定の妥当性: 目的に対して適切な技術・手法を採用しているか",
            "堅牢性: 既存の構成より障害耐性が向上しているか",
            "効率化: 運用コスト・工数が削減される見込みがあるか",
            "可観測性: 問題の検知・診断が容易な設計か",
            "自動化: 手作業が最小限に抑えられているか",
            "将来拡張性: 次の技術世代への移行を阻害しない設計か",
        ],
        minimum_score="全6項目のうち4項目以上クリア",
        gate_level="practical",
    ),
    extra_member_triggers=[],
    genealogy_depth=GenealogyDepth(max_elements=4, max_sources_per_element=2, include_cross_domain=True),
))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. 学習・教育・スキル開発
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_register(DomainConfig(
    domain_id="education",
    domain_name="学習・教育・スキル開発",
    team_name="Academy",
    team_motto="学びを設計し、成長を加速する",
    description="学習計画、教材開発、スキル習得、教育プログラム設計",
    specialist_members=[
        TeamMember(
            role_id="learning_designer",
            role_name="学習設計士",
            perspective="教育工学、カリキュラム設計、学習科学",
            prompt_directive=(
                "学習設計を実施せよ:\n"
                "1. 学習目標の構造化（Bloom's Taxonomy適用）\n"
                "2. 前提知識と到達目標のギャップ分析\n"
                "3. 最適な学習パス設計\n"
                "4. アクティブラーニング手法の選定\n"
                "5. 効果測定方法の設計"
            ),
        ),
        TeamMember(
            role_id="content_curator",
            role_name="コンテンツキュレーター",
            perspective="教材品質、情報の正確性、学習効率",
            prompt_directive=(
                "学習リソースを設計せよ:\n"
                "1. 最良の学習リソース（書籍、コース、論文）の調査と推奨\n"
                "2. 学習段階別のコンテンツ構成\n"
                "3. 実践演習・プロジェクト課題の設計\n"
                "4. つまずきやすいポイントの予測と対策"
            ),
        ),
    ],
    phases=[
        DomainPhase(
            name="Phase 1: 現状把握 + 学問系譜マッピング",
            description="学ぶべき領域の全体像と知識の発展系譜を把握する",
            tasks=[
                "対象領域の全体像のマッピング",
                "現在の習熟度の自己評価フレームワーク",
                "目標スキルレベルの定義",
                "最良の学習リソースのサーベイ",
                "学習スタイル・制約の把握",
                "【系譜統合】Phase 0の系譜分析を学習設計に接続 — この知識体系はどのように発展してきたか",
                "【系譜統合】学問の発展順序と学習の最適順序の対応を分析（歴史的発展≠最適学習パス だが文脈理解に有効）",
            ],
            output="memory/learning_goals.md",
        ),
        DomainPhase(
            name="Phase 2: カリキュラム設計",
            description="効率的な学習パスを構築する",
            tasks=[
                "学習トピックの依存関係グラフ作成",
                "段階別のマイルストーン設定",
                "各段階の教材・演習の設計",
                "スケジュール策定",
            ],
            output="memory/curriculum.md",
        ),
        DomainPhase(
            name="Phase 3: 実践・演習",
            description="手を動かして定着させる",
            tasks=[
                "実践プロジェクトの実施",
                "理解度チェックポイント",
                "つまずきの記録と対策",
                "応用課題への挑戦",
            ],
            output="memory/practice_log.md",
        ),
        DomainPhase(
            name="Phase 4: 統合・応用",
            description="学んだことを実践で使う",
            tasks=[
                "実プロジェクトへの適用",
                "知識の体系化・自分のことばでの整理",
                "他者への教示（学びの定着）",
                "次の学習目標の設定",
            ],
            output="memory/integration.md",
        ),
    ],
    innovation_gate=InnovationGate(
        gate_name="Academy Gate",
        criteria=[
            "学習対象の理解: 学ぶべき知識体系の構造と重点が把握されているか",
            "目標明確性: 到達目標が具体的かつ測定可能か",
            "効率性: 既存の学習パスより効率的なアプローチになっているか",
            "実践性: 座学だけでなく手を動かす要素があるか",
            "適応性: 学習者のペースや理解度に合わせた調整が可能か",
            "視野の広さ: 関連分野の知見も取り入れて理解を深める工夫があるか",
        ],
        minimum_score="全6項目のうち4項目以上クリア",
        gate_level="practical",
    ),
    extra_member_triggers=[
        {
            "condition": "プログラミング・技術スキルの学習",
            "member": TeamMember(
                role_id="coding_mentor",
                role_name="コーディングメンター",
                perspective="プログラミング教育、ペアプログラミング",
                prompt_directive="段階的なコーディング演習、コードレビュー課題を設計せよ。",
            ),
        },
    ],
    genealogy_depth=GenealogyDepth(max_elements=3, max_sources_per_element=1, include_cross_domain=False),
))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. 自動化・効率化
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_register(DomainConfig(
    domain_id="automation",
    domain_name="自動化・効率化",
    team_name="Clockwork",
    team_motto="人間は創造に集中する",
    description="ワークフロー自動化、RPA、ツール連携、プロセス最適化",
    specialist_members=[
        TeamMember(
            role_id="process_analyst",
            role_name="プロセスアナリスト",
            perspective="業務プロセスの分析・最適化",
            prompt_directive=(
                "プロセス分析を実施せよ:\n"
                "1. 現行プロセスの可視化（As-Is）\n"
                "2. ボトルネック・無駄の特定\n"
                "3. 自動化候補の優先順位付け（ROI算出）\n"
                "4. 理想プロセスの設計（To-Be）\n"
                "5. ヒューマンインザループの最適配置"
            ),
        ),
        TeamMember(
            role_id="integration_specialist",
            role_name="システム連携スペシャリスト",
            perspective="API連携、データパイプライン",
            prompt_directive=(
                "システム連携を設計せよ:\n"
                "1. 連携対象システムのAPI/インターフェース調査\n"
                "2. データフロー設計\n"
                "3. エラーハンドリング・リトライ戦略\n"
                "4. 監視・アラート設計"
            ),
        ),
    ],
    phases=[
        DomainPhase(
            name="Phase 1: プロセス分析 + 系譜統合",
            description="現行プロセスを可視化し、自動化技術の発展系譜の中で最適手法を特定する",
            tasks=[
                "現行プロセスの詳細マッピング",
                "時間・コスト・エラー率の計測",
                "類似の自動化事例のサーベイ",
                "ツール・技術の候補調査",
                "ROI試算",
                "【系譜統合】Phase 0の系譜分析を自動化技術史に接続 — RPA→AI自動化→自律エージェントの発展段階のどこを狙うか",
                "【系譜統合】他業界の自動化成功パターンを分析し、転用可能な手法を特定",
            ],
            output="memory/process_analysis.md",
        ),
        DomainPhase(
            name="Phase 2: 設計",
            description="自動化ソリューションを設計する",
            tasks=[
                "自動化アーキテクチャの設計",
                "ツール・技術の最終選定",
                "例外ケースの処理設計",
                "段階的導入計画",
            ],
            output="memory/automation_design.md",
        ),
        DomainPhase(
            name="Phase 3: 実装",
            description="動く自動化を構築する",
            tasks=[
                "コア自動化の実装",
                "テスト（正常系/異常系/境界値）",
                "既存システムとの結合テスト",
                "パフォーマンス検証",
            ],
            output="memory/implementation.md",
        ),
        DomainPhase(
            name="Phase 4: 運用・改善",
            description="安定運用と継続的改善",
            tasks=[
                "運用モニタリング設定",
                "効果測定（導入前後の比較）",
                "ユーザーフィードバック収集",
                "イテレーション改善",
            ],
            output="memory/operations.md",
        ),
    ],
    innovation_gate=InnovationGate(
        gate_name="Clockwork Gate",
        criteria=[
            "効果: 手動と比較して明確な時間削減・品質向上が見込めるか",
            "信頼性: エラー率が手動以下に抑えられるか",
            "拡張性: 将来のプロセス変更に対応できる設計か",
            "保守性: 自動化の仕組み自体が理解・修正しやすいか",
            "段階的導入: 一気に全置換せず、段階的に移行できる設計か",
            "費用対効果: 自動化の構築・保守コストが手動運用のコストを下回るか",
        ],
        minimum_score="全6項目のうち4項目以上クリア",
        gate_level="practical",
    ),
    extra_member_triggers=[],
    genealogy_depth=GenealogyDepth(max_elements=4, max_sources_per_element=2, include_cross_domain=True),
))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. コミュニティ・ソーシャル
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_register(DomainConfig(
    domain_id="social",
    domain_name="コミュニティ・ソーシャル",
    team_name="Agora",
    team_motto="つながりから価値を生む",
    description="コミュニティ構築、SNS戦略、イベント、コラボレーション",
    specialist_members=[
        TeamMember(
            role_id="community_strategist",
            role_name="コミュニティ戦略家",
            perspective="コミュニティ設計・エンゲージメント・成長戦略",
            prompt_directive=(
                "コミュニティ戦略を設計せよ:\n"
                "1. ターゲットコミュニティの特性分析\n"
                "2. エンゲージメントモデルの設計\n"
                "3. 成長戦略（バイラル係数、ネットワーク効果）\n"
                "4. コンテンツ戦略\n"
                "5. コミュニティヘルスの指標設計"
            ),
        ),
    ],
    phases=[
        DomainPhase(
            name="Phase 1: コミュニティ調査 + 系譜統合",
            description="対象コミュニティを理解し、コミュニティ形成の歴史的パターンを把握する",
            tasks=[
                "ターゲット層の分析",
                "既存コミュニティ/競合の調査",
                "プラットフォーム選定",
                "成功事例のケーススタディ",
                "【系譜統合】Phase 0の系譜分析をコミュニティ発展史に接続 — サロン→フォーラム→SNS→DAO の系譜のどこに位置するか",
                "【系譜統合】過去のコミュニティ盛衰パターン（成長→成熟→衰退→再生）から学ぶべき教訓を抽出",
            ],
            output="memory/community_research.md",
        ),
        DomainPhase(
            name="Phase 2: 設計",
            description="コミュニティの仕組みを設計する",
            tasks=[
                "ガバナンスモデルの設計",
                "エンゲージメント施策の設計",
                "コンテンツ計画",
                "成長ロードマップ",
            ],
            output="memory/community_design.md",
        ),
        DomainPhase(
            name="Phase 3: 立ち上げ",
            description="コミュニティを始動する",
            tasks=[
                "初期メンバー獲得施策",
                "ローンチコンテンツ準備",
                "運営体制の確立",
            ],
            output="memory/launch.md",
        ),
        DomainPhase(
            name="Phase 4: 成長・安定",
            description="持続的な成長を実現する",
            tasks=[
                "エンゲージメント指標の計測と改善",
                "コミュニティイベントの実施",
                "メンバー間のコラボ促進",
            ],
            output="memory/growth.md",
        ),
    ],
    innovation_gate=InnovationGate(
        gate_name="Agora Gate",
        criteria=[
            "価値提案: メンバーが得られる具体的な価値が明確か",
            "差別化: 既存コミュニティにない独自の価値があれば加点（必須ではない）",
            "持続性: 運営者依存でなく自律的に回る仕組みがあるか",
            "参加設計: 新規メンバーが参加しやすい導線があるか",
            "ネットワーク効果: メンバー増加で価値が向上する構造か",
            "安全性: 荒らし・トラブルへの対処設計があるか",
        ],
        minimum_score="全6項目のうち4項目以上クリア",
        gate_level="moderate",
    ),
    extra_member_triggers=[],
    genealogy_depth=GenealogyDepth(max_elements=3, max_sources_per_element=1, include_cross_domain=False),
))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. データ・AI / 機械学習
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_register(DomainConfig(
    domain_id="data_ai",
    domain_name="データ・AI / 機械学習",
    team_name="Neural",
    team_motto="データに語らせ、AIで飛躍する",
    description="機械学習モデル開発、データパイプライン、AI応用",
    specialist_members=[
        TeamMember(
            role_id="ml_architect",
            role_name="ML/AIアーキテクト",
            perspective="モデル選定、学習パイプライン、評価戦略",
            prompt_directive=(
                "ML/AI設計を実施せよ:\n"
                "1. タスク定義と評価指標の設定\n"
                "2. SOTA（State-of-the-Art）手法のサーベイ\n"
                "3. データ要件の定義と調達方法\n"
                "4. モデルアーキテクチャの候補比較\n"
                "5. 学習・推論パイプラインの設計"
            ),
        ),
        TeamMember(
            role_id="data_engineer",
            role_name="データエンジニア",
            perspective="データ収集・前処理・品質管理",
            prompt_directive=(
                "データパイプラインを設計せよ:\n"
                "1. データソースの特定と品質評価\n"
                "2. 前処理パイプラインの設計\n"
                "3. データ拡張戦略\n"
                "4. バージョニング・再現性の確保\n"
                "5. プライバシー・倫理的配慮"
            ),
        ),
    ],
    phases=[
        DomainPhase(
            name="Phase 1: 問題定義とサーベイ + 系譜統合",
            description="AI/MLの最前線と技術系譜を統合的に把握しタスクを定義する",
            tasks=[
                "問題の形式化（分類/回帰/生成/etc）",
                "SOTA手法と最新論文のサーベイ",
                "利用可能なデータセットの調査",
                "既存モデル/APIの調査（再利用可能性）",
                "評価指標とベースラインの設定",
                "【系譜統合】Phase 0の系譜分析をAI/ML技術史に接続 — この手法はML発展の系譜のどの段階にあるか",
                "【系譜統合】AI/MLの主要パラダイムシフト（記号AI→統計ML→深層学習→基盤モデル→...）の文脈で位置づけ",
                "【系譜統合】隣接分野（認知科学、神経科学、情報理論）からの知見移転候補を特定",
            ],
            output="memory/ml_survey.md",
        ),
        DomainPhase(
            name="Phase 2: データ・実験設計",
            description="データとの実験パイプラインを構築する",
            tasks=[
                "データ収集・前処理パイプラインの構築",
                "実験管理環境のセットアップ",
                "ベースラインモデルの実装・評価",
                "アブレーションスタディの設計",
            ],
            output="memory/experiment_setup.md",
        ),
        DomainPhase(
            name="Phase 3: モデル開発",
            description="最適なモデルを開発・チューニングする",
            tasks=[
                "アーキテクチャ実装",
                "ハイパーパラメータ最適化",
                "評価と比較分析",
                "エラー分析と改善",
            ],
            output="memory/model_development.md",
        ),
        DomainPhase(
            name="Phase 4: デプロイ・運用",
            description="モデルを実環境で稼働させる",
            tasks=[
                "推論パイプラインの最適化",
                "デプロイ環境の構築",
                "モニタリング（ドリフト検知等）",
                "A/Bテスト設計",
            ],
            output="memory/deployment.md",
        ),
    ],
    innovation_gate=InnovationGate(
        gate_name="Neural Gate",
        criteria=[
            "系譜的位置づけ: AI/MLパラダイムの発展系譜の中で何を前進させるか明確か",
            "技術的新規性: 系譜分析で特定されたフロンティアに踏み込んでいるか",
            "クロスドメイン知見: 隣接分野（認知科学、神経科学等）の知見が活用されているか",
            "データ戦略: 競合が容易にアクセスできないデータ優位性があるか",
            "実用性: 学術的な面白さだけでなく実用価値があるか",
            "倫理性: バイアス、公平性、プライバシーへの配慮があるか",
        ],
        minimum_score="全6項目のうち5項目以上クリア",
        gate_level="strict",
    ),
    extra_member_triggers=[
        {
            "condition": "大規模言語モデル（LLM）の活用",
            "member": TeamMember(
                role_id="llm_specialist",
                role_name="LLMスペシャリスト",
                perspective="プロンプト工学、RAG、ファインチューニング",
                prompt_directive="LLM活用戦略、プロンプト設計、RAGアーキテクチャを提案せよ。",
            ),
        },
    ],
    genealogy_depth=GenealogyDepth(max_elements=5, max_sources_per_element=3, include_cross_domain=True),
))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 11. プライベート / アダルト
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_register(DomainConfig(
    domain_id="private",
    domain_name="プライベート",
    team_name="Sanctuary",
    team_motto="自由な創作を、安全な場所で",
    description="成人向けゲーム・NSFW コンテンツ・プライベートプロジェクト（一般ゲームとは隔離）",
    specialist_members=[
        TeamMember(
            role_id="adult_game_designer",
            role_name="成人向けゲームデザイナー",
            perspective="ゲームメカニクス・シナリオ・キャラクター設計（成人向け特有のジャンル知識）",
            prompt_directive=(
                "成人向けゲームのコンセプトを設計せよ:\n"
                "1. ジャンル定義（VN/RPG/シミュレーション/etc）とターゲット層\n"
                "2. コアゲームループとエンゲージメントフック\n"
                "3. シナリオ構造とキャラクター設計\n"
                "4. 実装技術スタック選定（Ren'Py / Unity / RPGツクール / Godot 等）\n"
                "5. スコープ管理 — ソロ開発で完成可能な規模に絞る"
            ),
        ),
        TeamMember(
            role_id="content_strategist",
            role_name="コンテンツストラテジスト",
            perspective="配布戦略・プラットフォーム規約・収益化・コミュニティ管理",
            prompt_directive=(
                "配布・収益化戦略を設計せよ:\n"
                "1. 対応プラットフォーム（DLsite / itch.io / BOOTH / Patreon 等）と規約確認\n"
                "2. 価格戦略と無料/有料の切り分け\n"
                "3. 年齢確認・地域制限への対応\n"
                "4. コミュニティ管理とフィードバック収集\n"
                "5. プライバシー保護（制作者情報の匿名化等）"
            ),
        ),
    ],
    phases=[
        DomainPhase(
            name="Phase 1: コンセプト設計 + 系譜統合",
            description="ジャンル・スコープ・技術スタックを決定する",
            tasks=[
                "ジャンルとターゲット層の定義",
                "参考作品のリサーチと差別化ポイントの特定",
                "技術スタック選定と開発環境構築",
                "スコープ定義（MVPとフル版の切り分け）",
                "【系譜統合】Phase 0の系譜分析を成人向けゲーム史に接続 — このジャンルの発展でどこに位置するか",
            ],
            output="memory/concept.md",
        ),
        DomainPhase(
            name="Phase 2: 開発",
            description="シナリオ・アセット・実装を進める",
            tasks=[
                "シナリオ・スクリプト執筆",
                "キャラクター・背景アセット制作または調達",
                "コア実装（ゲームループ・UI）",
                "セーブ/ロード・設定機能の実装",
            ],
            output="memory/development_log.md",
        ),
        DomainPhase(
            name="Phase 3: テスト・リリース",
            description="品質確認と配布準備",
            tasks=[
                "プレイテストと不具合修正",
                "プラットフォーム規約チェック",
                "配布パッケージ作成",
                "ストアページ・紹介文の準備",
            ],
            output="memory/release.md",
        ),
    ],
    innovation_gate=InnovationGate(
        gate_name="Sanctuary Gate",
        criteria=[
            "完成可能性: ソロまたは少人数で実際に完成できるスコープか",
            "差別化: 同ジャンルの既存作品にない要素が1つ以上あるか",
            "配布戦略: 対象プラットフォームと規約が明確か",
        ],
        minimum_score="全3項目のうち2項目以上クリア",
        gate_level="practical",
    ),
    extra_member_triggers=[],
    genealogy_depth=GenealogyDepth(max_elements=3, max_sources_per_element=1, include_cross_domain=False),
))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ヘルパー関数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_domain(domain_id: str) -> DomainConfig | None:
    return DOMAINS.get(domain_id)


def get_all_domain_ids() -> list[str]:
    return list(DOMAINS.keys())


def get_domain_summary() -> str:
    """分類プロンプトに渡すドメイン一覧"""
    lines = []
    for d in DOMAINS.values():
        lines.append(f'- "{d.domain_id}": {d.domain_name} — {d.description}')
    return "\n".join(lines)


def build_team_roster(domain: DomainConfig, extra_members: list[TeamMember] | None = None) -> list[TeamMember]:
    """コアメンバー + ドメイン専門家 + 追加メンバーを統合"""
    roster = list(CORE_MEMBERS) + list(domain.specialist_members)
    if extra_members:
        roster.extend(extra_members)
    return roster


def format_team_roster_markdown(domain: DomainConfig, extra_members: list[TeamMember] | None = None) -> str:
    """チーム編成をMarkdown表として出力"""
    roster = build_team_roster(domain, extra_members)
    lines = [
        f"## チーム「{domain.team_name}」 — {domain.team_motto}\n",
        "| # | 役職 | 視点・専門 |",
        "|---|------|-----------|",
    ]
    for i, m in enumerate(roster, 1):
        lines.append(f"| {i} | **{m.role_name}** | {m.perspective} |")

    if domain.extra_member_triggers:
        lines.append("")
        lines.append("### 追加要員トリガー")
        lines.append("内容に応じて以下の専門家が自動参加する:")
        for t in domain.extra_member_triggers:
            lines.append(f"- **{t['member'].role_name}** — 条件: {t['condition']}")

    lines.append("")
    lines.append("*内容の複雑さに応じて、上記以外の専門家も柔軟に追加可能。"
                 "追加が必要と判断した場合はその役割と理由を明示してチームに加えること。*")
    return "\n".join(lines)


def format_phases_markdown(domain: DomainConfig) -> str:
    """Phase 0（系譜分析）+ ドメイン固有フェーズをMarkdown形式で出力"""
    lines = []

    # Phase 0: 系譜分析（全ドメイン共通）
    lines.append(f"### {GENEALOGY_PHASE.name}")
    lines.append(f"**目標**: {GENEALOGY_PHASE.description}\n")
    lines.append("> 画家が評価される作品を生むために美術史の系譜を深く理解するように、")
    lines.append("> あらゆる分野で「発展の文脈の中に位置づける」ことが進歩の条件である。")
    lines.append("> このフェーズは全ドメイン共通の最重要フェーズであり、省略不可。\n")
    # ドメイン別深度設定を表示（LLMエージェントへの指示として機能）
    depth = domain.genealogy_depth
    cross = "あり" if depth.include_cross_domain else "なし"
    lines.append(
        f"**深度設定**: 要素上限 {depth.max_elements} 個 / "
        f"要素ごとMCP検索ソース上限 {depth.max_sources_per_element} / "
        f"クロスドメイン調査（Step 4）: {cross}\n"
    )
    for task in GENEALOGY_PHASE.tasks:
        lines.append(f"- {task}")
    lines.append(f"\n**成果物**: `{GENEALOGY_PHASE.output}`\n")

    # ドメイン固有フェーズ
    for i, phase in enumerate(domain.phases):
        lines.append(f"### {phase.name}")
        lines.append(f"**目標**: {phase.description}\n")
        if i == 0:
            # Phase 1（最初のドメイン固有フェーズ）: genealogy.md 参照を義務化
            lines.append(
                "- **【前提】** `memory/genealogy.md` を読み込み、系譜研究員の分析"
                "（フロンティア・未解決領域）を踏まえた上で以下のタスクを実施すること"
            )
        for task in phase.tasks:
            lines.append(f"- {task}")
        lines.append(f"\n**成果物**: `{phase.output}`\n")

    return "\n".join(lines)



def format_innovation_gate_markdown(domain: DomainConfig) -> str:
    """イノベーションゲートをMarkdown形式で出力"""
    gate = domain.innovation_gate
    level = gate.gate_level

    lines = [f"## Innovation Gate: {gate.gate_name}\n"]

    if level == "strict":
        lines.append("**Phase 2 → Phase 3 移行前に必ず以下を全て評価すること。**\n")
        lines.append("### 大原則: 目的の本質が最優先\n")
        lines.append(
            "このゲートの目的は「アイディアの核」に記された目的を最善の形で達成することである。"
        )
        lines.append(
            "新規性・差別化・系譜的ポジショニングは目的達成の**手段**であり、それ自体が目的ではない。"
        )
        lines.append(
            "目的の本質から遠ざかる新規性は**却下**するか、**ユーザーの判断**に委ねること。\n"
        )
    elif level == "moderate":
        lines.append("**Phase 2 → Phase 3 移行前に以下を評価すること。**\n")
        lines.append("### 大原則: 本質の達成が最優先\n")
        lines.append(
            "このゲートの目的は「アイディアの核」に記された目的を達成することである。"
        )
        lines.append(
            "系譜分析でより新しい手法・ツールが見つかった場合は報告すること。"
            "便利な機能付加やトークン節約策があれば提案すること。"
        )
        lines.append(
            "独自性・新しい視点は**歓迎するが必須ではない**。"
            "独自性の追求が本質を損なう場合は、本質を優先すること。\n"
        )
    else:  # practical
        lines.append("**Phase 2 → Phase 3 移行前に以下を確認すること。**\n")
        lines.append("### 大原則: 実用性と改善効果が最優先\n")
        lines.append(
            "このゲートの目的は「アイディアの核」に記された目的を**確実に・実用的に**達成することである。"
        )
        lines.append(
            "系譜分析でより新しい手法・ツールが見つかった場合は報告すること。"
            "導入時に便利な機能付加やトークン節約策があれば提案すること。"
        )
        lines.append(
            "ただし新規性・差別化はゲート通過の必須条件ではない。"
            "既存の優れた手法・実績あるアプローチの活用を推奨する。\n"
        )

    # Step 1: 本質整合性チェック
    lines.append("### Step 1: 本質整合性チェック（前提条件）\n")
    lines.append("以下を全て確認するまで Step 2 に進んではならない。\n")
    lines.append(
        "1. **目的一貫性**: handoff.md「アイディアの核」に記された目的・課題が、"
        "現在の設計でも中心に据えられているか"
    )
    if level == "strict":
        lines.append(
            "2. **手段と目的の逆転がないか**: 新規性・差別化の追求が目的化し、"
            "元の課題解決を後退させていないか"
        )
    elif level == "moderate":
        lines.append(
            "2. **手段と目的の逆転がないか**: 独自性の追求が目的化し、"
            "元の課題解決を後退させていないか"
        )
    else:
        lines.append(
            "2. **過剰設計がないか**: 必要以上に複雑な仕組みを導入し、"
            "シンプルな課題解決を後退させていないか"
        )
    lines.append(
        "3. **ユーザー価値の保持**: 最初に想定された受益者が、"
        "現在の設計でも明確に恩恵を受けるか"
    )
    lines.append(
        "4. **複雑化の正当性**: Phase 1-2 で追加された要素は全て"
        "元の目的達成に寄与しているか\n"
    )
    lines.append(
        "**不合格の場合**: 「アイディアの核」に立ち返り、"
        "本質から逸脱した要素を除去してから再評価する。\n"
    )

    # Step 2: ドメイン基準評価
    lines.append(f"### Step 2: ドメイン基準評価（合格基準: {gate.minimum_score}）\n")
    if level == "strict":
        lines.append(
            "本質整合性を確認した上で、以下の基準を評価する。"
        )
        lines.append(
            "**ただし、基準を満たすために本質から逸脱する変更を加えてはならない。**"
        )
        lines.append(
            "基準と本質が矛盾する場合は、本質を優先しユーザーに判断を仰ぐこと。\n"
        )
    elif level == "moderate":
        lines.append(
            "本質整合性を確認した上で、以下の基準を評価する。"
        )
        lines.append(
            "独自性に関する項目は加点要素として扱い、未達でも他の基準で補えれば通過可能。\n"
        )
    else:
        lines.append(
            "本質整合性を確認した上で、以下の実用性基準を評価する。"
        )
        lines.append(
            "既存手法の適切な活用も高く評価する。車輪の再発明は不要。\n"
        )

    for i, c in enumerate(gate.criteria, 1):
        lines.append(f"{i}. {c}")
    lines.append("")

    # フッター
    if level == "strict":
        lines.append(
            "**ゲート不合格の場合**: Phase 1-2 に戻り、本質を保ったまま不足項目を補強する。"
        )
        lines.append(
            "ゲートの評価結果は `memory/innovation_gate.md` に記録すること"
            "（本質整合性チェック結果を含む）。"
        )
        lines.append(
            "**妥協してゲートを通過させない。ただし本質を歪めてゲートを通過させることも同様に禁止する。**"
        )
    elif level == "moderate":
        lines.append(
            "**ゲート不合格の場合**: Phase 1-2 に戻り、本質を保ったまま不足項目を補強する。"
        )
        lines.append(
            "ゲートの評価結果は `memory/innovation_gate.md` に記録すること。"
        )
        lines.append(
            "**本質の達成を最優先し、独自性は「あればより良い」として扱うこと。**"
        )
    else:
        lines.append(
            "**ゲート不合格の場合**: Phase 1-2 に戻り、実用性・改善効果の観点で不足項目を補強する。"
        )
        lines.append(
            "ゲートの評価結果は `memory/innovation_gate.md` に記録すること。"
        )
        lines.append(
            "**「確実に動く・使える・役に立つ」が最優先。過剰な作り込みより早期の実用化を重視する。**"
        )

    return "\n".join(lines)


def format_genealogy_framework_markdown(domain: DomainConfig) -> str:
    """系譜分析フレームワーク概要（handoff.md用）— ドメイン別深度設定を含む"""
    depth = domain.genealogy_depth
    cross = "あり" if depth.include_cross_domain else "なし"

    return (
        "## 系譜分析フレームワーク（Genealogy Framework）\n\n"
        "全プロジェクト共通の根幹フレームワーク。Phase 0 として必ず最初に実行する。\n"
        "アイディアを「発展の文脈の中に位置づける」ことで、立ち上げ時点で分野の最先端に立つことを目指す。\n\n"
        "**実行者**: 系譜研究員（genealogist）サブエージェント\n"
        "**出力**: `memory/genealogy.md`\n"
        f"**このドメインの深度設定**: 要素上限 {depth.max_elements} 個 / "
        f"要素ごとMCP最大 {depth.max_sources_per_element} ソース / "
        f"クロスドメイン調査（Step 4）: {cross}\n\n"
        "**以降の全フェーズ**: `memory/genealogy.md` を読み込み、フロンティア分析を踏まえて作業を進めること\n\n"
        "> 画家が評価される作品を生むために美術史の系譜を深く理解するように、\n"
        "> あらゆる分野で「発展の文脈の中に位置づける」ことが進歩の条件である。\n"
    )
