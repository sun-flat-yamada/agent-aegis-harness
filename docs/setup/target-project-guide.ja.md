---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "DOC-SETUP-TARGET-001-JA"
title: "監査対象プロジェクトへの導入 & ツール計装ガイド"
version: "1.1.0"
status: "active"
language: "ja"
canonical_ref: "docs/setup/target-project-guide.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "windsurf", "cli"]
  min_aah_version: "0.1.0"
tags: ["setup", "target-project", "hooks", "antigravity", "claude-code", "github-copilot", "copilot-app", "copilot-cli"]
---

# 監査対象プロジェクトへの導入 & ツール計装ガイド

本ガイドは、既存の開発プロジェクトに Agent Aegis Harness (`aah`) を装着し、開発者の業務摩擦（Flow State の阻害）を最小限に抑えつつ AI エージェントの挙動を計装・統制する手順を解説します。

---

## 1. クイックインストールと自動化の内訳

### 1.1 コマンド実行

プロジェクト環境にハーネスをインストールし、リポジトリルートで初期化を実行します：

```bash
# 開発用依存関係としてインストール
pip install agent-aegis-harness

# リポジトリルートでガバナンスバンドルを初期化
aah init
```

### 1.2 `aah init` による全自動配備とユーザー個別作業の境界線

利用者から頻繁に寄せられる疑問として、**「`aah init` を実行するだけで全自動で完了するのか、それともユーザーが個別にファイル編集や設定変更を行う必要があるのか」** という点があります。

境界線は以下の通り明確に分かれています：

- **`aah init` が全自動で行うこと（自動配備）:**
  1. **ガバナンス資産ディレクトリの作成**: `.aegis/rules/`（ポリシー）、`.aegis/schemas/`（JSONスキーマ）、`.aegis/templates/`、`.aegis/logs/`、`.aegis/instructions/`、`.hooks/`、`.skills/` を一括作成。
  2. **共通設定の初期化**: `.aegis/config.yaml` が存在しない場合、デフォルトの監視レベル・設定を自動生成。
  3. **個別指示ルールファイルの配置**: `.aegis/instructions/aegis-copilot-rules.md`、`aegis-claude-rules.md`、`aegis-system-governance.md` を生成。
  4. **非破壊ポインタインジェクション（既存設定の保持）**: 既存の AI 設定ファイルを検知し、既存の指示を上書き・破壊することなく末尾に 1 行の参照ポインタを安全に追加（ファイルが存在しない場合は新規作成）：
     - `.github/copilot-instructions.md` (GitHub Copilot 用)
     - `CLAUDE.md` (Claude Code 用)
     - `.cursorrules` (Cursor 用)
     - `.amazonq/rules.md` (Amazon Q / AWS Kiro 用)
  5. **フックスクリプトの生成**: `.hooks/pre-agent-execution.sh` および `.hooks/post-agent-execution.sh` を自動生成。
  6. **ポリシーバンドルの暗号学的ハッシュ算出**: ルールおよびスキーマの決定論的 SHA-256 ダイジェストを算出。

- **`aah init` では行えないこと（ユーザーが個別に行う必要がある作業）:**
  - **Git へのコミット・プッシュ**: `aah init` はローカルファイルを生成・追記しますが、**`git add` / `git commit` / `git push` は自動実行しません**。リポジトリへの反映は利用者が行う必要があります。
  - **外部ツール設定ファイルの編集**: リポジトリ外のユーザーディレクトリにある設定（Claude Code の `~/.claude/settings.json` や、シェルのプロファイル `~/.bashrc` / `$PROFILE`）は、セキュリティ上自動変更できないため利用者が登録します。
  - **IDE のワークスペース設定**: VS Code の `.vscode/settings.json` への MCP Gateway 連携設定など、エディタ固有のオプション設定。
  - **クラウド CI/CD パイプラインの配備**: GitHub Copilot App 等のクラウドエージェントを保護するための GitHub Actions ワークフロー（`.github/workflows/`）。
  - **Python SDK コードへの組み込み**: 自作の Antigravity エージェントプログラムにフックアダプタをインポートして呼び出す実装。

### 1.3 ツール別自動化対応・個別作業マトリクス

| AI ツール / インターフェース | `aah init` での自動化範囲 | ユーザー個別作業の要否 | 主な設定ファイル / 実行コマンド |
| :--- | :--- | :--- | :--- |
| **GitHub Copilot (IDE)** | 指示ポインタの非破壊注入 | **要** (Gitコミット、任意でMCP・Gitフック設定) | `.github/copilot-instructions.md`, `.vscode/settings.json` |
| **GitHub Copilot App (Web/PR)** | 指示ポインタの非破壊注入 | **要** (デフォルトブランチへの反映、CI設定) | `.github/workflows/aegis-sentinel.yml` |
| **GitHub Copilot CLI** | 対象外 (CLI実行系) | **要** (コマンドの wrap 実行、シェルエイリアス設定) | `aah wrap -- gh copilot ...`, シェルプロファイル |
| **Google Antigravity** | スキル・ルール資産の配備 | **要** (SDKコードでのアダプタ登録 / IDEスキル認識) | Python エージェント初期化コード / IDE設定 |
| **Claude Code** | ポインタ注入、`.hooks/` 生成 | **要** (Claude 設定へのフックコマンド登録) | `~/.claude/settings.json` |
| **Cursor & Windsurf** | `.cursorrules` へのポインタ注入 | **任意** (`aah wrap` の強制プロンプト追記) | `.cursorrules` |
| **汎用 CLI / 自作スクリプト** | 対象外 | **要** (実行時に `aah wrap` を付与) | ターミナルコマンド |

---

## 2. ツール別詳細計装手順

### A. GitHub Copilot (IDE: VS Code / JetBrains / Visual Studio)

VS Code や JetBrains などのエディタ上で動作する GitHub Copilot (Chat, Inline, Edit) に対する計装です。

#### 1. `aah init` が自動で行うこと:
`.github/copilot-instructions.md` に以下の参照ポインタを非破壊で自動追記（または新規作成）します：
```markdown
<!-- AEGIS-AUDIT-INJECTION -->
Please strictly follow Aegis Governance Rules in `.aegis/instructions/aegis-copilot-rules.md`.
```

#### 2. 利用者が個別に実施する作業:

- **ステップ 1: 指示ファイルとルールを Git にコミットする**  
  GitHub Copilot 拡張機能は、ワークスペースのリポジトリから指示を読み込みます。生成されたファイルをコミットしてください：
  ```bash
  git add .github/copilot-instructions.md .aegis/
  git commit -m "chore(aegis): instrument GitHub Copilot workspace instructions"
  ```

- **ステップ 2 (推奨): VS Code MCP Security Gateway を設定する**  
  Copilot Chat が MCP 経由でツール実行（コマンド実行やファイル変更）を行う際、Aegis Sentinel の即時事前検閲を通過させるため、`.vscode/settings.json` に設定を追加します：
  ```json
  {
    "github.copilot.advanced": {
      "mcpServers": {
        "aegis": {
          "type": "stdio",
          "command": "aah",
          "args": ["mcp-server", "--mode", "local"]
        }
      }
    }
  }
  ```
  *(社内共有の Aegis Cloud MCP Gateway を利用する場合は `"type": "sse", "url": "https://aegis-mcp.enterprise.internal/v1/mcp"` を指定).*

- **ステップ 3 (推奨): Git Post-Commit 監査バインドアダプタを導入する**  
  Copilot が生成・支援した変更をコミットした際、直前の AI 対話監査ハッシュを Git コミットメタデータ（`git notes`）に自動紐付けするため、`.git/hooks/post-commit` を作成します：
  ```bash
  #!/usr/bin/env bash
  python -c "from aegis.recorder.git_correlator import GitCorrelator; GitCorrelator().run_post_commit()"
  ```
  実行権限を付与します：`chmod +x .git/hooks/post-commit`。

---

### B. GitHub Copilot App (GitHub.com Web, PR レビュー, Copilot Workspace, Coding Agent)

GitHub.com 上で動作するプルリクエスト自動レビュー、Copilot Workspace、および自律コーディングエージェント（GitHub Copilot App）に対する統制です。クラウド上で自律稼働するため、開発者のローカルフックは呼び出されません。

#### 1. `aah init` が自動で行うこと:
- GitHub.com がリポジトリ共通指示として公式認識する `.github/copilot-instructions.md` を配備します。

#### 2. 利用者が個別に実施する作業:

- **ステップ 1: デフォルトブランチ (`main` / `master`) へプッシュする**  
  > [!IMPORTANT]
  > GitHub.com 上のクラウド Copilot エージェント（PR レビューや Copilot Workspace）は、**リポジトリのデフォルトブランチにある `.github/copilot-instructions.md` のみを読み込みます**。  
  > 未マージのフィーチャーブランチにのみ配置されている場合、クラウドエージェントには指示が伝わりません。

  ```bash
  git checkout main
  git merge <初期化を行ったブランチ>
  git push origin main
  ```

- **ステップ 2: サーバーサイド CI 統制ゲート（Tier 3 Sentinel）を配備する**  
  クラウドエージェントはローカル端末のフックを経由せずにブランチや PR を作成するため、PR 作成時に CI パイプライン上で Sentinel 検査を実行することが必須となります。
  
  `.github/workflows/aegis-sentinel.yml` を作成します：
  ```yaml
  name: Aegis Sentinel Governance Gate

  on:
    pull_request:
      branches: [main, master]

  jobs:
    sentinel-audit:
      name: Aegis Sentinel Verification
      runs-on: ubuntu-latest
      steps:
        - name: Check out repository
          uses: actions/checkout@v4

        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: "3.10"

        - name: Install Aegis Harness
          run: pip install agent-aegis-harness

        - name: Run Sentinel Instant Audit
          run: aah check --strict
  ```

- **ステップ 3: Branch Protection Rules (保護ブランチルール) で必須化する**  
  GitHub リポジトリの **Settings > Branches > Branch protection rules** にて、`Aegis Sentinel Verification` ジョブのパスをマージ必須条件に設定します。これにより、ポリシー違反を含む Copilot 生成コードのマージが自動遮断されます。

---

### C. GitHub Copilot CLI (`gh copilot`)

ターミナル内でコマンド提案や解説を行う GitHub CLI 拡張機能（`gh copilot suggest`, `gh copilot explain`）に対する計装です。

#### 1. `aah init` が自動で行うこと:
- なし（CLI プロセスは独立したコマンドとして実行されるため）。

#### 2. 利用者が個別に実施する作業:

- **ステップ 1: `aah wrap` でコマンドを保護実行する**  
  `gh copilot` コマンドの先頭に `aah wrap --` を付与して実行します。Sentinel が提案・実行されるコマンドを事前検閲し、危険なコマンド（`rm -rf /` やシークレット漏洩等）を即時遮断するとともに、5W1H 監査ログを記録します：
  ```bash
  # コマンド提案の検閲・保護実行
  aah wrap -- gh copilot suggest -t shell "空のログディレクトリを検索して削除する"

  # コマンド解説の検閲・監査記録
  aah wrap -- gh copilot explain "find . -type f -exec chmod 644 {} +"
  ```

- **ステップ 2: シェルエイリアス・ラッパー関数を設定する (推奨)**  
  毎回 `aah wrap --` を手動入力する手間を省くため、シェルの設定ファイルにエイリアスを追記します：

  - **Bash (`~/.bashrc`) または Zsh (`~/.zshrc`):**
    ```bash
    # Aegis 保護付き GitHub Copilot CLI
    alias gh-copilot='aah wrap -- gh copilot'
    alias ghcs='aah wrap -- gh copilot suggest -t shell'
    alias ghce='aah wrap -- gh copilot explain'
    ```

  - **PowerShell (`$PROFILE`):**
    ```powershell
    function gh-copilot { aah wrap -- gh copilot @args }
    function ghcs { aah wrap -- gh copilot suggest -t shell @args }
    function ghce { aah wrap -- gh copilot explain @args }
    ```

- **ステップ 3: `gh copilot alias` を利用している場合の統合**  
  すでに `eval "$(gh copilot alias -- bash)"` などの公式エイリアス展開を利用している場合は、展開後の関数呼び出しが `aah wrap` を経由するよう設定してください。

---

### D. Google Antigravity (SDK / IDE)

Google Antigravity 環境では、二段階ガバナンスとライフサイクルフックを活用します。

#### 1. `aah init` が自動で行うこと:
- `.skills/` および `.aegis/rules/` にポリシー定義資産を配置。

#### 2. 利用者が個別に実施する作業:

- **Python SDK を利用する場合**: 自作エージェントの初期化コードに `AntigravityAegisAdapter` を登録します：
  ```python
  from aegis.recorder.antigravity_adapter import AntigravityAegisAdapter
  from google.antigravity.sdk import LocalAgentConfig

  def configure_agent():
      config = LocalAgentConfig()
      adapter = AntigravityAegisAdapter(repo_path=".")
      config.hooks = adapter.register_hooks(config.hooks)
      return config
  ```
  これにより、以下が自動キャプチャされます：
  - `pre_turn`: プロンプトのサニタイズおよびインジェクション検査
  - `pre_tool_call_decide`: Sentinel Tier 1 による危険コマンド即時遮断
  - `post_tool_call`: ファイル変更差分の記録
  - `on_compaction`: コンテキスト圧縮時のドリフト評価

- **Antigravity IDE を利用する場合**: ワークスペース内の `.agents/skills` または `.skills/` にガバナンススキル（`antigravity-two-phase-governance`, `dev-change-lifecycle`）が認識されていることを確認します。

---

### E. Claude Code

Claude Code は `CLAUDE.md` による指示読み込みと、ライフサイクルフックに対応しています。

#### 1. `aah init` が自動で行うこと:
- `CLAUDE.md` に以下の参照ポインタを非破壊追記（または新規作成）：
  ```markdown
  <!-- AEGIS-AUDIT-INJECTION -->
  @.aegis/instructions/aegis-claude-rules.md
  ```
- `.hooks/pre-agent-execution.sh` および `.hooks/post-agent-execution.sh` を生成。

#### 2. 利用者が個別に実施する作業:
Claude の設定ファイル（`~/.claude/settings.json` またはプロジェクト内 `.claude/config.json`）にフックを登録します：
```json
{
  "hooks": {
    "pre_tool_call": "./.hooks/pre-agent-execution.sh",
    "post_tool_call": "./.hooks/post-agent-execution.sh"
  }
}
```

---

### F. Cursor & Windsurf

Cursor および Windsurf では、ワークスペース単位のルールファイルを利用します。

#### 1. `aah init` が自動で行うこと:
- `.cursorrules` に以下の参照ポインタを非破壊追記（または新規作成）：
  ```markdown
  # <!-- AEGIS-AUDIT-INJECTION -->
  # Follow .aegis/instructions/aegis-system-governance.md
  ```

#### 2. 利用者が個別に実施する作業:
コマンド実行の強制保護を行いたい場合、`.cursorrules` に以下を追記してエージェントに指示します：
```markdown
破壊的コマンドの実行や広範囲のファイル変更を行う前に、必ず以下を経由して実行してください:
  aah wrap -- <コマンド>
```

---

### G. 汎用 CLI / 自作スクリプト

LLM を呼び出す任意のスクリプトやカスタム CLI に対する計装です。

#### 1. `aah init` が自動で行うこと:
- なし。

#### 2. 利用者が個別に実施する作業:
コマンド実行時に先頭へ `aah wrap` を付与します：
```bash
aah wrap -- claude "src/auth.py の脆弱性を修正して"
aah wrap -- python my_agent_script.py --run
```

---

## 3. 健全性確認 & 診断コマンド

自動セットアップおよび個別作業の完了後、以下のコマンドで計装状況を検証します：

### 3.1 計装状況の確認 (`aah status`)
`aah status` を実行し、全ツールの指示ポインタ、MCP Security Gateway、および監査ログの状態を確認します：
```bash
aah status
```
期待される出力例：
```text
                     Aegis Multi-AI Instrumentation Status                      
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Component           ┃ Target / Mode                    ┃ Status              ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ Claude Code Pointer │ CLAUDE.md                        │ ACTIVE              │
│ VSCode Copilot Pntr │ .github/copilot-instructions.md  │ ACTIVE              │
│ AWS Kiro / Q Pointer│ .amazonq/rules.md                │ ACTIVE              │
│ Cursor Pointer      │ .cursorrules                     │ ACTIVE              │
│ MCP Gateway         │ Local (Default: STDIO)           │ READY               │
│ Local SQLite WAL    │ aegis_wal.db                     │ ONLINE              │
└─────────────────────┴──────────────────────────────────┴─────────────────────┘
```

### 3.2 即時監査スキャン (`aah check`)
`aah check` を実行し、ポリシーバンドルの暗号学的ハッシュ検証とシークレット検査を行います：
```bash
aah check
```
すべての項目が `PASSED` と表示されれば、Sentinel 統制が有効です。

### 3.3 MCP セキュリティゲートウェイ検証 (`aah mcp-server --test`)
Copilot や Claude で MCP Gateway を利用する場合、事前検閲テストを実行して安全な操作の許可と危険な操作の遮断を確認します：
```bash
aah mcp-server --test
```
