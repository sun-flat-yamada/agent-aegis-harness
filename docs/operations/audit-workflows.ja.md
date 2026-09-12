---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "DOC-OPS-WORKFLOWS-001-JA"
title: "監査実施ワークフロー & フォレンジック調査運用ガイド"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: "docs/operations/audit-workflows.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.1.0"
tags: ["operations", "audit", "workflows", "forensics", "ci-gate"]
---

# 監査実施ワークフロー & フォレンジック調査運用ガイド

本ガイドは、セキュリティ担当者や監査員が、リアルタイム評価、CI/CD 自動ゲート、暗号学的改ざん検証、およびインシデントフォレンジック調査を実施するための実務ワークフローを定めます。

## 1. 監査ユースケース一覧

| ユースケース | 実行契機 | 目的・対象 | 使用コマンド |
| :--- | :--- | :--- | :--- |
| **UC-1: CI/CD Gate リアルタイム監査** | コミット時 / PR 作成時 | 危険操作・シークレット漏洩の自動遮断 | `aah check --strict` |
| **UC-2: 暗号完全性・改ざん検証** | 定期バッチ / 監査実施時 | Hash Chain の数学的連続性立証 | `aah verify --log-file <path>` |
| **UC-3: インシデントフォレンジック** | セキュリティ事故発生時 | AI の全推論過程・生差分の完全再現 | `grep trace_id forensic-trail.jsonl` |
| **UC-4: ガバナンスレポーティング** | 週次・月次監査報告 | ISO 42001 指標準拠レポート出力 | `aah report -o report.md` |

---

## 2. 各ワークフローの具体的手順

### UC-1: CI/CD 自動監査ゲート
GitHub Actions や CI パイプライン内で以下を実行します：
```bash
aah check --strict
```
- **終了コード 0**: 全ポリシー合格。マージ可能。
- **終了コード 1**: 警告または BLOCK 違反を検知。PR のマージを自動的に阻止。

### UC-2: Hash Chain 改ざん検証 (Archivist)
監査ログファイルの暗号学的完全性を検証します：
```bash
aah verify --log-file .aegis/logs/audit-trail.jsonl
```
1バイトでも改ざんや欠損、行順の入替えが存在した場合、即座にブロック番号を特定して終了コード 2 で停止します。

### UC-3: インシデントフォレンジック調査 (5W1H 深層解明)
不審な操作や事故が発生した場合：
1. `audit-trail.jsonl` から該当事象の `trace_id` を抽出。
2. `forensic-trail.jsonl` から完全証跡を検索：
   ```bash
   grep "<trace_id>" .aegis/logs/forensic-trail.jsonl | jq .
   ```
3. AI がどのような思考（`reasoning_summary`）を経てコマンドを実行したか、入力プロンプトと環境メタデータを完全に特定します。

### UC-4: ISO 42001 エグゼクティブレポート出力
経営層・監査役向けの週次要約レポートを出力します：
```bash
aah report -o .aegis/reports/weekly-audit.md
```
イベント総数、ブロック阻止件数、ポリシーダイジェスト整合状況が Markdown およびコンソールテーブルで出力されます。
