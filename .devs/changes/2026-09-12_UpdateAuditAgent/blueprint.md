---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "architecture_doc"
id: "BLUEPRINT-AUDIT-AGENT-001"
title: "Agent Aegis Harness (aah) - Automated Multi-Agent Audit Collection Blueprint: Hybrid Active-Skills & Passive-Monitoring Architecture (VSCode Copilot, Claude Code, AWS Kiro, and CLI)"
version: "1.1.0"
status: "active"
language: "ja"
canonical_ref: "docs/BLUEPRINT_UPDATE_AUDIT_AGENT.md"
hash_digest: "sha256:pending"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "windsurf", "aws-kiro", "cli"]
  min_aah_version: "0.3.0"
tags: ["blueprint", "audit-agent", "hybrid-capture", "github-copilot", "claude-code", "aws-kiro", "mcp", "cloud-mcp", "telemetry", "git-hooks", "non-destructive", "governance"]
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
---

# Agent Aegis Harness (aah) - マルチAI自動監査記録・収集基盤 技術設計書 (Blueprint)

**Document ID:** BLUEPRINT-AUDIT-AGENT-001 | **Version:** 1.1.0 | **Status:** Active | **Author:** @sun-flat-yamada (Youhei Yamada)  
**Target Change:** `.devs/changes/2026-09-12_UpdateAuditAgent`

---

## 1. エグゼクティブサマリー & 確定要件定義

### 1.1 変更の背景と課題意識
`agent-aegis-harness (aah)` のこれまでの設計では、明示的に `aah wrap -- <command>` を実行するか、Google Antigravity SDK のライフサイクルフックに直接統合することで監査記録（5W1H、推論根拠、ハッシュ連鎖）を記録してきました。

しかし、実際のエンタープライズ現場（100PJ × 数十名規模）において、開発者が日常的に使用する AI 支援ツールは多岐にわたります。
- **VSCode での GitHub Copilot / Copilot Chat / Copilot Edit**（エディタ内蔵・インライン補完）
- **GitHub Copilot CLI / GitHub Copilot App**（スタンドアロンアプリ / ターミナル）
- **Claude Code (Anthropic)**（CLI型自律開発エージェント、ローカルセッション永続化）
- **AWS Kiro / Amazon Q Developer**（AWS エコシステム直結のコーディングエージェント）
- **Cursor / Windsurf / Antigravity**（AI Native IDE / エージェントランタイム）

日常の開発において、開発者に「AI ツールを使うたびに手動でラッパーを通す」「手動で監査コマンドを打つ」ことを強いる運用は、開発者体験（Flow State）を著しく損ない、**「ラッパーを通さないシャドーAI利用」や監査ログの欠損**を招きます。

したがって、監査対象プロジェクトに `aah init` を適用した後は、**開発者が普段どおりに VSCode Copilot、Claude Code、AWS Kiro などを利用するだけで、意識することなく裏側で自動的に監査証跡が保存・収集・暗号封印される仕組み**が不可欠です。

### 1.2 確定したアーキテクチャ方針 (合意事項)
ユーザーとのディスカッションを経て、以下の 4 大基本方針を確定としました。

| 論点領域 | 確定方針 | 採択理由・仕様概要 |
| :--- | :--- | :--- |
| **【論点 1】VSCode Copilot インライン補完** | **案 A: 採用確定＆Git コミット相関型** | キーストローク毎のプロキシは行わず、実際に採用され Git コミットに至ったコード差分を直近の AI セッションと相関付け。開発者マシンの遅延 0ms と無駄なログ容量爆発（GB級/日）を完全抑止。 |
| **【論点 2】監視エージェント稼働形態** | **案 A: イベント駆動型 Harvester ＋ Git フック** | OS のファイル変更通知（inotify / ReadDirectoryChangesW）または Git コミット契機でのみ動作（メモリ < 20MB、CPU ほぼ 0%）。常駐サービスへの心理的抵抗や権限問題を解消。 |
| **【論点 3】MCP ゲートウェイ適用形態** | **案 A: 推奨利用<br>＋ Local MCP デフォルト<br>＋ Cloud MCP 選択可能** | ・**デフォルト:** 端末内ローカル STDIO/SSE で即座に動作する Local MCP サーバー。<br>・**エンタープライズ拡張:** 設定 1 行で全社共通の Cloud MCP サーバー（Azure Container Apps / ECS 等）へ切り替え可能。 |
| **【指示ファイル配備方式】** | **独自 Instruction 完全分離 ＋ 1行非破壊インジェクション** | 既存の `CLAUDE.md` や `copilot-instructions.md` 等を**絶対に強制上書きしない**。独自命令を `.aegis/instructions/` に完全分離し、既存ファイルの末尾に 1 行の参照ポインタのみを安全に追加。 |

---

## 2. コアコンセプト: ハイブリッド二重捕捉モデル (Dual-Vector Adaptive Audit)

本設計では、「能動的ルール・スキル配備（Active）」と「透過的外部監視（Passive）」を融合した **ハイブリッド二重捕捉アーキテクチャ（Dual-Vector Adaptive Audit: DVAA）** を採用します。

```mermaid
flowchart TB
    subgraph Vector1 ["Vector 1: 能動的プロトコル層 (Active In-Agent Protocol)"]
        direction TB
        V1_1["独自 Instruction 完全分離配備<br/>(.aegis/instructions/aegis-rules.md)"]
        V1_2["非破壊 1行ポインタ・インジェクション<br/>(CLAUDE.md, copilot-instructions.md 等の末尾へ追加)"]
        V1_3["Aegis MCP Security Gateway<br/>(Local デフォルト / Cloud 切り替え可能)"]
        V1_4["思考過程 (Why) & 計画の自律報告"]
    end

    subgraph Vector2 ["Vector 2: 透過的受動監視層 (Passive Out-of-Band Interception)"]
        direction TB
        V2_1["Local Session Harvester (Daemon)<br/>(~/.claude/projects, VSCode workspaceStorage)"]
        V2_2["CLI / Shell Shim & Wrapper<br/>(claude, gh copilot, q 透過実行)"]
        V2_3["Git Commit Correlation Hook<br/>(pre-commit / post-commit 暗号バインド)"]
    end

    subgraph AegisCore ["Aegis Core 統合・正規化・封印エンジン"]
        direction TB
        Norm["NormalizedAIEvent 変換器<br/>(マルチツールの 5W1H 統一スキーマ化)"]
        Sentinel["Sentinel 即時検閲 & Redactor<br/>(シークレット・PII・禁止コマンド遮断)"]
        WAL["Local-First SQLite WAL & Merkle Chain<br/>(即時ハッシュ連結・耐改ざん性保証)"]
    end

    Vector1 -->|思考・意図・計画 (Why)| Norm
    Vector2 -->|実行事実・ツール呼出・コード差分 (What/How)| Norm
    Norm --> Sentinel
    Sentinel --> WAL
```

1. **Active (能動的) 層:**
   - リポジトリ導入時に、Aegis 専用の監査命令ファイル群（`.aegis/instructions/`）を安全に配備。
   - 既存の各種 AI ツール定義ファイルの末尾に、Aegis 命令を読み込ませる **1 行のインポート/ポインタ行** を安全にインジェクト。
   - エージェントに「Aegis 監査下にあること」を認知させ、変更意図・計画・思考過程（CoT）を出力させる。
   - さらに、**Aegis MCP Security Gateway** を提供し、ツール呼び出しをインターセプトして Sentinel 検閲を実行。
2. **Passive (受動的) 層:**
   - ルールの無視、インライン補完、外部アプリの利用があっても漏れなく捕捉するため、**ローカルセッション監視デーモン（Harvester）**、**MCP 透過プロキシ**、および **Git Commit 相関フック** が物理的な実行ログ・コード差分を透過的にキャプチャ。
3. **Correlation (相関) 層:**
   - 能動的に得られた「AI の意図・思考（Why）」と、受動的に得られた「実行結果・コード変更（What/How）」をタイムスタンプおよびセッション ID で暗号学的に突合し、Merkle Hash Chain に封印。

---

## 3. 業界最新動向・事例調査 (State of the Art 2025-2026)

最新の AI 支援開発環境におけるロギング、拡張性、およびガバナンスの動向を整理しました。

| ツール / 領域 | アーキテクチャ特性 | 監査ログ採取の接点 (Hook Points) | 最新動向 & ベストプラクティス |
| :--- | :--- | :--- | :--- |
| **Anthropic Claude Code** | ・ターミナル型自律エージェント<br>・リポジトリ内 `CLAUDE.md` 自動読込<br>・Native MCP クライアント機能<br>・全セッションをローカル永続化 | ・`~/.claude/projects/<hash>/sessions/*.jsonl`<br>・MCP Server 設定 (`.claude/config.json`)<br>・Tool 呼出フック | Claude Code は全対話、思考、ツール呼出をローカル JSONL に完全記録している。ファイル監視（inotify / ReadDirectoryChangesW）によるリアルタイム追跡（tailing）が最も高信頼。 |
| **GitHub Copilot (VSCode)** | ・VSCode 拡張機能として動作<br>・インライン補完（Ghost Text）<br>・Copilot Chat / Edit / Agent Mode | ・`.github/copilot-instructions.md`<br>・VSCode `workspaceStorage/` のチャット履歴<br>・GitHub Enterprise Audit Log API | インライン補完の全プロンプト監視はノイズが膨大。**「Chat セッションログ採取」＋「Git コミット時の採用差分相関」** で捉えるのが定石。 |
| **GitHub Copilot CLI / App** | ・ターミナルコマンド提案 / 実行<br>・デスクトップアプリ / Web 統合 | ・Shell Wrapper (`gh copilot` alias)<br>・GitHub CLI 拡張フック | シェルラッパー / Shim（`preexec` フック等）でコマンド呼出と実行結果を透過的にインターセプト。 |
| **AWS Kiro / Amazon Q Developer** | ・IDE 拡張 & CLI & AWS コンソール<br>・プロジェクトルール (`.amazonq/` or `.aws/`) | ・`~/.aws/q/` ローカルログ<br>・AWS CloudTrail / CloudWatch Logs | プロジェクト内ルール定義による能動誘導に加え、エンタープライズでは AWS CloudTrail 側のイベント連携が可能。 |
| **共通標準: MCP (Model Context Protocol)** | ・Anthropic 主導のオープン標準<br>・Claude Code, Cursor, Windsurf, VSCode 等が対応 | ・MCP Tool / Resource / Prompt 呼び出し<br>・Stdio / SSE / HTTP プロトコル | **2025-2026 年最大の潮流。** Aegis 自体を「MCP Security Gateway」として稼働させることで、全ツールのファイル編集・Bash 実行をプロトコルレベルで一括検閲・記録可能。 |

---

## 4. アーキテクチャ決定記録 (ADR: Architectural Decision Records)

### ADR-01: 能動的ルール配備（Active）と外生受動的捕捉（Passive）のハイブリッド統合
- **ステータス:** 承認 (Approved)
- **決定:** ハイブリッド方式（Dual-Vector Adaptive Audit）を採用する。能動的指示注入で「意図・思考（Why）」を採取し、受動的監視で「実行事実・コード差分（What/How）」を漏れなく捕捉して相関付ける。

### ADR-02: VSCode Copilot インライン補完（Ghost Text）の捕捉粒度（案 A 確定）
- **ステータス:** 承認 (Approved)
- **決定:** 
  - インライン補完は「エディタで実際に確定・コミットされたコード差分」を対象に、Git Commit Correlation Hook で捕捉する。
  - Copilot Chat / Edit / Agent Mode は、セッション単位で全対話・プロンプト・回答をローカルストレージから完全記録する。
- **根拠:** キーストローク毎のプロキシは不要な通信遅延と日次ギガバイト級のノイズログを生むため。

### ADR-03: MCP Security Gateway の「Local デフォルト ＋ Cloud 選択可能」アーキテクチャ
- **ステータス:** 承認 (Approved)
- **決定:**
  - **Local MCP サーバー（デフォルト）:** `aah mcp-server` コマンドによりローカル STDIO/SSE で即座に動作。外部通信不要・完全オフライン対応。
  - **Cloud MCP サーバー（選択可能）:** `.aegis/config.yaml` の設定変更により、全社統合の Cloud MCP サーバー（Azure Container Apps / AWS ECS / Google Cloud Run 等）に接続可能とする。mTLS / Bearer Token による安全な認証を実装。
- **関連ドキュメント:** Cloud MCP サーバーの構築手順書を `docs/setup/cloud-mcp-server-guide.md`（および日本語版）として作成する。

### ADR-04: クライアント側監視アーキテクチャ（案 A 確定: 超軽量 Harvester ＋ Git フック）
- **ステータス:** 承認 (Approved)
- **決定:** 常駐重厚デーモンではなく、OS の低負荷ファイル変更検知（inotify / ReadDirectoryChangesW）または Git コミット契機でのみ動作する超軽量 Harvester（メモリ < 20MB）を採用する。

### ADR-05: 独自 Instruction 完全分離 ＋ 1行非破壊インジェクション方式
- **ステータス:** 承認 (Approved)
- **背景:** 監査対象プロジェクトには既存の `CLAUDE.md` や `.github/copilot-instructions.md` が既に運用されている可能性が高く、上書きすると既存の業務コンテキストを破壊してしまう。
- **決定:**
  - Aegis 専用の監査規約ファイルは `.aegis/instructions/` 配下に完全分離して格納する（例: `.aegis/instructions/aegis-system-governance.md`）。
  - 対象ツールのグローバル定義ファイル（`CLAUDE.md`, `.github/copilot-instructions.md`, `.amazonq/rules.md` 等）の**末尾に、本監査規約を参照させる 1 行のポインタ行のみを安全に追加（Append）**する。
  - 既にポインタ行が存在する場合はスキップする冪等性（Idempotency）を保証する。

---

## 5. 指示ファイル非破壊インジェクション設計 (Non-Destructive Injector)

### 5.1 ディレクトリ構成と分離モデル
```text
<target-project>/
├── .aegis/
│   ├── config.yaml
│   └── instructions/                           # 【完全分離】Aegis 独自監査規約
│       ├── aegis-system-governance.md          # 共通監査・5W1H 記録プロトコル
│       ├── aegis-claude-rules.md               # Claude Code 向け固有規約
│       └── aegis-copilot-rules.md              # GitHub Copilot 向け固有規約
│
├── CLAUDE.md                                   # 既存ファイルを保持
│   └── [末尾に 1 行追加]
│       <!-- AEGIS-AUDIT-INJECTION -->
│       @.aegis/instructions/aegis-claude-rules.md
│
└── .github/
    └── copilot-instructions.md                 # 既存ファイルを保持
        └── [末尾に 1 行追加]
            <!-- AEGIS-AUDIT-INJECTION -->
            Please strictly follow Aegis Governance Rules defined in `.aegis/instructions/aegis-copilot-rules.md`.
```

### 5.2 各ツールへのインジェクション仕様一覧

| 対象ツール | 既存ファイルパス | 挿入される 1 行ポインタ構文 | ファイル未存在時の動作 |
| :--- | :--- | :--- | :--- |
| **Claude Code** | `CLAUDE.md` | `@.aegis/instructions/aegis-claude-rules.md` | 新規作成し上記 1 行のみを記述 |
| **GitHub Copilot (VSCode)** | `.github/copilot-instructions.md` | `Strictly follow rules in .aegis/instructions/aegis-copilot-rules.md` | 新規作成し上記 1 行のみを記述 |
| **AWS Kiro / Q** | `.amazonq/rules.md` | `Refer and enforce: .aegis/instructions/aegis-system-governance.md` | 新規作成し上記 1 行のみを記述 |
| **Cursor / Windsurf** | `.cursorrules` / `.windsurfrules` | `# Aegis: Read and follow .aegis/instructions/aegis-system-governance.md` | 新規作成し上記 1 行のみを記述 |

### 5.3 冪等性（Idempotency）保証アルゴリズム
- インジェクターは、対象ファイルに対象マーカー（例: `AEGIS-AUDIT-INJECTION`）が既に存在するかを検査。
- 存在する場合は一切の変更を行わず、存在しない場合のみ末尾に改行とポインタ行を追記する。
- 既存のプロジェクト設定や指示を 1 文字たりとも削除・改変しない。

---

## 6. MCP Security Gateway アーキテクチャ (Local デフォルト & Cloud 選択可能)

### 6.1 デュアルモード構成図

```mermaid
flowchart TD
    subgraph Client ["開発者環境 (Developer Machine)"]
        Agent["AI エージェント (Claude Code / Copilot / Cursor)"]
        ClientConfig[".aegis/config.yaml<br/>mcp.mode = 'local' or 'cloud'"]

        subgraph LocalMode ["Mode 1: Local MCP (デフォルト)"]
            LocalServer["aah mcp-server (Local In-Process / Stdio)<br/>・完全オフライン対応<br/>・遅延 < 1ms<br/>・ローカル SQLite WAL 連携"]
        end
    end

    subgraph CloudInfra ["エンタープライズ クラウド基盤 (Azure / AWS / GCP)"]
        subgraph CloudMode ["Mode 2: Cloud MCP Server (設定で切り替え可能)"]
            Gateway["Cloud API Gateway / Reverse Proxy (mTLS / OIDC 認証)"]
            CloudMCP["Aegis Cloud MCP Container Service<br/>(Azure Container Apps / AWS ECS / Cloud Run)"]
            CentralPolicy["中央 Policy GitOps 配布"]
            CentralStorage["Azure Blob Immutable WORM / S3 Lock"]
        end
    end

    Agent -->|STDIO / SSE| LocalServer
    Agent -.->|HTTPS / SSE (Bearer Token)| Gateway
    Gateway --> CloudMCP
    CloudMCP --> CentralPolicy
    CloudMCP --> CentralStorage
```

### 6.2 接続設定仕様 (`.aegis/config.yaml`)
```yaml
version: "1.3.0"
repository_id: "my-service-app"

mcp_gateway:
  # 動作モード: "local" (デフォルト) または "cloud"
  mode: "local"

  local:
    transport: "stdio" # [stdio | sse]
    log_level: "info"
    tools_whitelist:
      - "read_file"
      - "write_file"
      - "run_command"
      - "git_diff"

  cloud:
    # クラウド MCP サーバーのエンドポイント (HTTPS)
    endpoint: "https://aegis-mcp.enterprise.internal/v1/mcp"
    auth:
      type: "bearer_token" # [bearer_token | oidc | mtls]
      token_env_var: "AEGIS_CLOUD_MCP_TOKEN"
    tls_verify: true
    timeout_sec: 5
    fallback_to_local_on_error: true # クラウド障害時は自動でローカルへフォールバック
```

### 6.3 Local vs Cloud の機能比較表

| 評価項目 | Local MCP サーバー (Default) | Cloud MCP サーバー (Enterprise Option) |
| :--- | :--- | :--- |
| **起動方式** | `aah mcp-server` (STDIO/SSE) | クラウドコンテナ (HTTPS/SSE) |
| **インフラコスト** | **$0 (ゼロインフラ)** | コンテナ実行費用 (月額数千円〜) |
| **ネットワーク要件** | **完全オフライン動作可能** | 社内ネットワークまたは VPN/閉域網接続 |
| **ポリシー集中管理** | ローカル Git 同期に依存 | クラウド側で即時一元更新・全社一斉適用 |
| **ログ集約** | ローカル WAL 蓄積 → バッチ転送 | **リアルタイム直接クラウド格納** |
| **フォールバック** | - | クラウド障害時にローカルモードへ自動切替可能 |

---

## 7. 透過的モニタリング層 (Harvester & Git Hook)

### 7.1 Local Session Harvester Daemon
- **動作契機:**
  - OS ファイル変更イベント（inotify / ReadDirectoryChangesW）
  - 対象: `~/.claude/projects/*/sessions/*.jsonl`, VSCode `workspaceStorage/*/state.vscdb`
- **処理内容:**
  1. セッションファイルの差分（追加行）を検知。
  2. 会話プロンプト、AI の思考テキスト（Chain of Thought）、ツール呼出を抽出。
  3. `SensitiveRedactor` によるシークレット/PII マスキング。
  4. 共通スキーマ `NormalizedAIEvent` へ正規化。
  5. ローカル SQLite WAL (`aegis_wal.db`) に書き込み、Merkle Hash Chain にリアルタイム連結。

### 7.2 Git Commit Correlation Hook
- **`pre-commit`:** ステージング差分のシークレット漏洩検査（重大違反時は exit 1）。
- **`post-commit`:**
  - コミットハッシュ（Git SHA）を取得。
  - 直近 15 分以内の AI 監査イベントの最新 Merkle Root ハッシュを取得。
  - コミットと AI 監査ログをバインドした `CommitCorrelationRecord` を発行。
  - コミットの Git Notes または `.aegis/logs/audit-trail.jsonl` に暗号学的に封印。

---

## 8. ブートストラップ & 導入コマンド

```bash
# 1. 監査ハーネスの初期化（非破壊インジェクション & 独自設定配備）
aah init --tools=all

# 2. Local MCP サーバーの動作確認（デフォルト）
aah mcp-server --test

# 3. 監視デーモン（Harvester）のステータス確認
aah status

# 4. (オプション) Cloud MCP サーバーへの切り替え確認
aah config set mcp_gateway.mode cloud
aah check
```

---

## 9. ドキュメント体系 & 次のステップ

1. **Cloud MCP サーバー構築手順書の作成:**
   - ユーザー指示に基づき、`docs/setup/cloud-mcp-server-guide.md`（英語正本）および `docs/setup/cloud-mcp-server-guide.ja.md`（日本語版）を新規作成します。
   - 内容: Azure Container Apps / AWS ECS / Docker での構築、mTLS/OIDC 認証、高可用性設計、ローカルフォールバック。
2. **Stage 2: `spec.md` の策定:**
   - 非破壊インジェクターの正規表現・文字列マッチング仕様。
   - `NormalizedAIEvent` の Pydantic v2 スキーマ定義。
   - Harvester のファイルウォッチャー実装仕様。
