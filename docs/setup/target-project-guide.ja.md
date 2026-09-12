---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "DOC-SETUP-TARGET-001-JA"
title: "監査対象プロジェクトへの導入 & ツール計装ガイド"
version: "1.2.0"
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

### 1.2 初期化の全自動対応とユーザー独自定義時の必須要件

利用者から頻繁に寄せられる疑問として、**「`aah init` を実行するだけで全自動で完了するのか、それともユーザーが個別にファイル編集や設定変更を行う必要があるのか」** という点があります。

結論として、**日常の開発利用においては `aah init` の実行のみで全自動でセットアップが完了します。**

- **`aah init` が全自動で行うこと（自動配備）:**
  1. **ガバナンス資産ディレクトリの作成**: `.aegis/rules/`（ポリシー）、`.aegis/schemas/`（JSONスキーマ）、`.aegis/templates/`、`.aegis/logs/`、`.aegis/instructions/`、`.hooks/`、`.skills/` を一括作成。
  2. **共通設定の初期化**: `.aegis/config.yaml`（監視レベル、レコーダー設定）を自動生成。
  3. **個別指示ルールファイルの配置**: `.aegis/instructions/aegis-copilot-rules.md`、`aegis-claude-rules.md`、`aegis-system-governance.md` を生成。
  4. **非破壊ポインタインジェクション（既存プロンプトの維持）**: 既存の AI 設定ファイルを検知し、既存の指示を上書き・破壊することなく末尾に 1 行の参照ポインタを安全に追加（ファイルが存在しない場合は新規作成）：
     - `.github/copilot-instructions.md` (GitHub Copilot 用)
     - `CLAUDE.md` (Claude Code 用)
     - `.cursorrules` (Cursor 用)
     - `.amazonq/rules.md` (Amazon Q / AWS Kiro 用)
  5. **フックスクリプトの生成**: `.hooks/pre-agent-execution.sh` および `.hooks/post-agent-execution.sh` を自動生成。
  6. **ポリシーバンドルの暗号学的ハッシュ算出**: ルールおよびスキーマの決定論的 SHA-256 ダイジェストを算出。

サポートされている AI ツール（VS Code 等の GitHub Copilot、Claude Code、Cursor）は、ワークスペース内のこれらの指示ファイルを自律的に読み込むため、**リポジトリ外のユーザー設定や IDE 設定を手動編集する必要は一切ありません。**

- **ユーザーが独自に定義・カスタマイズを行う場合の必須要件:**
  リポジトリで独自に指示ファイルやポリシーをカスタマイズする場合は、以下のルールを遵守する必要があります：
  1. **インジェクションポインタの維持（必須）**: プロジェクト固有の指示を `.github/copilot-instructions.md`、`CLAUDE.md`、`.cursorrules` 等に追加・編集する場合、**Aegis インジェクションポインタ（`<!-- AEGIS-AUDIT-INJECTION -->`）を削除せず必ず維持してください**。このポインタが削除されると、AI エージェントがガバナンス規約をロードしなくなります。
  2. **カスタムポリシーのスキーマ適合（必須）**: `.aegis/rules/` 内にプロジェクト独自の監査ポリシー（YAML）を追加する場合、`.aegis/schemas/frontmatter.schema.json` に準拠したヘッダーメタデータを付与してください。
  3. **`aah check` による検証の必須実行**: ファイル編集後は必ず `aah check` を実行してください。強化された **Instruction Pointer Integrity（指示ポインタ完全性）検査** により、設定ファイル内で Aegis ポインタが誤って欠落・改ざんされていないかが自動検証されます。

### 1.3 ツール別自動化対応・独自定義時マトリクス

| AI ツール / インターフェース | `aah init` での自動化範囲 | ユーザー独自定義・変更時の必須要件 | 検証コマンド |
| :--- | :--- | :--- | :--- |
| **GitHub Copilot (IDE)** | 全自動（ポインタ注入） | `.github/copilot-instructions.md` 内のポインタを維持 | `aah check` / `aah status` |
| **GitHub Copilot App (Web/PR)** | 全自動（指示ファイル配備） | クラウドCI統制は構想設計書を参照 | `aah check --strict` |
| **GitHub Copilot CLI** | ラッパー実行 | 実行時に `aah wrap -- gh copilot ...` で保護 | `aah status` |
| **Claude Code** | 全自動（ポインタ注入） | `CLAUDE.md` 内のポインタを維持 | `aah check` / `aah status` |
| **Cursor & Windsurf** | 全自動（ポインタ注入） | `.cursorrules` 内のポインタを維持 | `aah check` / `aah status` |
| **Google Antigravity** | スキル・ルール資産配備 | Python SDK エージェントコードでアダプタ登録 | `aah check` |
| **汎用 CLI / 自作スクリプト** | ラッパー実行 | 実行時に `aah wrap -- <コマンド>` を付与 | `aah verify` |

---

## 2. ツール別詳細案内

### A. GitHub Copilot (IDE: VS Code / JetBrains / Visual Studio)

VS Code や JetBrains などのエディタ上で動作する GitHub Copilot (Chat, Inline, Edit) に対する計装です。

#### 1. セットアップと通常運用:
`aah init` により、以下のポインタが `.github/copilot-instructions.md` に自動設定されます：
```markdown
<!-- AEGIS-AUDIT-INJECTION -->
Please strictly follow Aegis Governance Rules in `.aegis/instructions/aegis-copilot-rules.md`.
```
VS Code や JetBrains の Copilot 拡張機能は、ワークスペース内のこのファイルを自動的にカスタム指示として読み込みます。手動での設定ファイル編集は不要です。

#### 2. 独自定義時の必須ルール:
チーム独自のコーディング規約を `.github/copilot-instructions.md` に追記・編集する場合は、Aegis インジェクションポインタのブロックを維持してください。`aah check` を実行することでポインタの存在が検証されます。

*(※発展的オプション: Copilot Chat の MCP ツール呼び出しをリアルタイム検閲したい場合、`.vscode/settings.json` に `"github.copilot.advanced": {"mcpServers": {"aegis": {"type": "stdio", "command": "aah", "args": ["mcp-server", "--mode", "local"]}}}` を設定できます)。*

---

### B. GitHub Copilot App (GitHub.com Web, PR レビュー, Copilot Workspace, Coding Agent)

GitHub.com 上で動作するプルリクエスト自動レビューや自律コーディングエージェント（GitHub Copilot App）に対する統制です。

#### 1. セットアップと通常運用:
- クラウド版 Copilot は、`aah init` で生成された `.github/copilot-instructions.md` をリポジトリ共通指示として読み込みます。

#### 2. クラウドワークフロー監査アーキテクチャ:
クラウドエージェントはリモートのエフェメラル実行環境（GitHub インフラ）上で稼働するため、ローカル端末のフックは呼び出されません。  
クラウドワークフローおよびリモートエージェントに対する専用の監査・CI統制アーキテクチャの全容は、技術構想設計書 [`.devs/changes/2026-09-12_AddSupportCloudFlowAudit/blueprint.md`](../../.devs/changes/2026-09-12_AddSupportCloudFlowAudit/blueprint.md) に規定されています。

---

### C. GitHub Copilot CLI (`gh copilot`)

ターミナル内でコマンド提案や解説を行う GitHub CLI 拡張機能（`gh copilot suggest`, `gh copilot explain`）に対する計装です。

#### 1. `aah wrap` によるコマンド保護実行:
`gh copilot` コマンドの先頭に `aah wrap --` を付与して実行します。Sentinel が提案・実行されるコマンドを事前検閲し、危険なコマンド（`rm -rf /` 等）を即時遮断するとともに、5W1H 監査ログを記録します：
```bash
# コマンド提案の検閲・保護実行
aah wrap -- gh copilot suggest -t shell "空のログディレクトリを検索して削除する"

# コマンド解説の検閲・監査記録
aah wrap -- gh copilot explain "kill -9 1234"
```

#### 2. 任意のシェルエイリアス設定:
入力を簡略化したい場合、シェルの設定ファイルにエイリアスを定義できます：
- **Bash / Zsh (`~/.bashrc`, `~/.zshrc`):**
  ```bash
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

---

### D. Google Antigravity (SDK / IDE)

#### 1. 通常運用:
`aah init` により、`.skills/` および `.aegis/rules/` にポリシー資産が自動配備されます。

#### 2. Python SDK での利用:
自作エージェントのスクリプトでは、`AntigravityAegisAdapter` をフックに登録します：
```python
from aegis.recorder.antigravity_adapter import AntigravityAegisAdapter
from google.antigravity.sdk import LocalAgentConfig

def configure_agent():
    config = LocalAgentConfig()
    adapter = AntigravityAegisAdapter(repo_path=".")
    config.hooks = adapter.register_hooks(config.hooks)
    return config
```

---

### E. Claude Code

#### 1. セットアップと通常運用:
`aah init` により、`CLAUDE.md` に以下の参照ポインタが自動設定されます：
```markdown
<!-- AEGIS-AUDIT-INJECTION -->
@.aegis/instructions/aegis-claude-rules.md
```
Claude Code 起動時に自動認識されるため、手動設定は不要です。

#### 2. 独自定義時の必須ルール:
`CLAUDE.md` を独自に編集する場合、`@.aegis/instructions/aegis-claude-rules.md` の参照行を維持してください。

---

### F. Cursor & Windsurf

#### 1. セットアップと通常運用:
`aah init` により、`.cursorrules` に以下のポインタが自動設定されます：
```markdown
# <!-- AEGIS-AUDIT-INJECTION -->
# Follow .aegis/instructions/aegis-system-governance.md
```

#### 2. 独自定義時の必須ルール:
`.cursorrules` を独自に編集する場合、Aegis ガバナンス規約の参照行を維持してください。

---

### G. 汎用 CLI / 自作スクリプト

LLM を呼び出す任意のスクリプトやカスタム CLI に対する計装です。先頭に `aah wrap` を付与して実行します：
```bash
aah wrap -- claude "src/auth.py の脆弱性を修正して"
aah wrap -- python my_agent_script.py --run
```

---

## 3. 健全性確認 & 診断コマンド

初期化後や設定変更後、以下のコマンドでプロジェクトの健全性を確認します：

### 3.1 計装状況の確認 (`aah status`)
`aah status` を実行し、全ツールの指示ポインタ、MCP Gateway、および監査ログの状態を確認します：
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
`aah check` を実行し、ポリシーバンドルのハッシュ検証、シークレット検査、および **Instruction Pointer Integrity（指示ポインタ完全性）** を検証します：
```bash
aah check
```
期待される出力例：
```text
[AUDIT] Running Sentinel Instant Audit...
                             Sentinel Audit Verdict                             
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Category                      ┃ Status ┃ Details                             ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ PII / Secret Redactor         │ PASSED │ Pattern rules active (0 leaks in    │
│                               │        │ git staged)                         │
│ Context Drift Integrity       │ PASSED │ Compaction drift score: 0.04        │
│                               │        │ (Threshold: 0.20)                   │
│ Instruction Pointer Integrity │ PASSED │ All 4 active instruction pointers   │
│                               │        │ verified                            │
│ Policy Digest Match           │ PASSED │ sha256:ed961461c97... (5 policies)  │
│ Skill Tool Whitelist          │ PASSED │ 10 tools approved in                │
│                               │        │ .aegis/rules/skill-compliance-poli… │
│ Cryptographic Log Chain       │ PASSED │ 3 blocks cryptographically verified │
└───────────────────────────────┴────────┴─────────────────────────────────────┘
[OK] All Sentinel Instant Audit gates passed.
```

独自定義の編集時に誤ってポインタが削除された場合、`Instruction Pointer Integrity` が警告を発見します：
`Missing Aegis pointer in: .github/copilot-instructions.md (Run 'aah init')`
