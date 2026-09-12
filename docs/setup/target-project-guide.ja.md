---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "DOC-SETUP-TARGET-001-JA"
title: "監査対象プロジェクトへの導入 & ツール計装ガイド"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: "docs/setup/target-project-guide.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.1.0"
tags: ["setup", "target-project", "hooks", "antigravity", "claude-code"]
---

# 監査対象プロジェクトへの導入 & ツール計装ガイド

本ガイドは、既存の開発プロジェクトに Agent Aegis Harness (`aah`) を装着し、開発者の摩擦を最小限に抑えつつ AI エージェントの挙動を計装・統制する手順を解説します。

## 1. クイックインストール

```bash
# 開発用依存関係としてインストール
pip install agent-aegis-harness

# リポジトリルートでガバナンスバンドルを初期化
aah init
```

`aah init` により、以下の構成が自動配備されます：
```text
.aegis/
├── config.yaml          # プロジェクト別監査設定
├── rules/               # 適用ポリシー (security, drift, compliance)
├── schemas/             # JSONスキーマ群 (audit-event, frontmatter)
├── templates/           # レポートテンプレート
└── logs/                # 監査ログ出力先
.hooks/                  # エージェント実行フック
.skills/                 # AIアシスタント向けスキル定義
```

---

## 2. ツール別計装手順

### A. Google Antigravity (SDK / IDE)
Antigravity 環境では、付属のアダプタをフックに登録するだけで自動計装されます：
```python
from aegis.recorder.antigravity_adapter import AntigravityAegisAdapter
from google.antigravity.sdk import LocalAgentConfig

def configure_agent():
    config = LocalAgentConfig()
    adapter = AntigravityAegisAdapter(repo_path=".")
    config.hooks = adapter.register_hooks(config.hooks)
    return config
```
以下が自動キャプチャされます：
- `pre_turn`: プロンプトのサニタイズおよびインジェクション検査
- `pre_tool_call_decide`: Sentinel Tier 1 による危険コマンド即時遮断
- `post_tool_call`: ファイル変更差分の記録
- `on_compaction`: コンテキスト圧縮時のドリフト評価

### B. Claude Code
`.hooks/pre-agent-execution.sh` および `.hooks/post-agent-execution.sh` を Claude 設定ファイル（`~/.claude/settings.json` 等）に登録します：
```json
{
  "hooks": {
    "pre_tool_call": "./.hooks/pre-agent-execution.sh",
    "post_tool_call": "./.hooks/post-agent-execution.sh"
  }
}
```

### C. Cursor & Windsurf
リポジトリ直下の `.cursorrules` にガバナンス規則を記載し、危険操作や実行時に `aah wrap` の介在を促します：
```markdown
破壊的コマンドの実行や広範囲のファイル変更を行う前に、以下で検証して実行してください:
  aah wrap -- <コマンド>
```

### D. 汎用 CLI / 自作スクリプト
任意の AI CLI コマンドの先頭に `aah wrap` を付与して実行します：
```bash
aah wrap -- claude "src/auth.py の脆弱性を修正して"
```

---

## 3. 健全性確認 (Smoke Test)

`aah check` を実行し、全ポリシーとマスキング機能が正常にロードされているか検証します：
```bash
aah check
```
すべての項目が `PASSED` と表示されれば、Sentinel 統制が有効です。
