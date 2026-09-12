---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "DOC-PORTAL-INDEX-JA"
title: "Agent Aegis Harness ドキュメントポータル"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: "docs/index.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor"]
  min_aah_version: "0.1.0"
tags: ["portal", "overview", "quickstart"]
---

# Agent Aegis Harness

**ソフトウェア開発AIのための自動評価・ガバナンス基盤**

---

## ようこそ

Agent Aegis Harness (`aah`) は、AI エージェント（Google Antigravity, Claude Code, GitHub Copilot, Cursor 等）のための包括的ガバナンス・可観測性ハーネスです。ルールハッシュによる決定論的再現性、暗号学的 Hash Chain による改ざん防止、3 段階多層防御 Sentinel、およびオフライン自己改善ループを提供します。

---

## コアコンポーネント

| コンポーネント | CLI コマンド | 概要 |
| :--- | :--- | :--- |
| **実行ラッパー** | `aah wrap` | AI エージェントの透過的実行と 5W1H 監査証跡の自動記録 |
| **Sentinel (監査員)** | `aah sentinel` | 3 段階多層防御（Tier 1 AST <10ms、Tier 2 小型モデル <100ms、Tier 3 LLM-Judge）と PII/シークレット即時マスキング |
| **Archivist (書記・台帳管理)** | `aah archivist` | ルール群の統合ハッシュ算出、Merkle Hash Chain 検証、監査再現性テスト |
| **Recorder (証跡記録)** | `aah recorder` | 5W1H 抽出とデュアルストリーム監査ログ、OpenTelemetry 転送 |
| **Refiner (改善・最適化)** | `aah refiner` | オフラインクラスタ分析によるルール・スキル改善 PR 自動生成 |
| **Reporter (レポート)** | `aah report` | ISO/IEC 42001 & NIST AI RMF 準拠ガバナンスレポート |

---

## クイックスタート

```bash
# インストール
pip install agent-aegis-harness

# ガバナンスバンドルの初期化
aah init

# Sentinel 統制下での実行
aah wrap -- antigravity run

# 監査ログの改ざん検証
aah verify --log-file .aegis/logs/audit-trail.jsonl
```

---

## ドキュメントガイド

### :material-architecture: [アーキテクチャ & システム設計](ARCHITECTURE.ja.md)
システムアーキテクチャ全体像、コンポーネント間相互作用、データフロー図。

### :material-gavel: 設計意思決定記録 (ADR)
- [ADR-0001: 暗号学的 Hash Chain による監査ログ不変性の担保](adr/0001-immutable-audit-log.ja.md)
- [ADR-0002: 監査実行と自己改善ループの疎結合分離](adr/0002-decoupled-refinement.ja.md)
- [ADR-0003: 利用者ペルソナ別 3 分類ドキュメント階層の採用](adr/0003-three-tiered-documentation.ja.md)

### :material-cog: 運用 & ワークフロー
- [監査実施ユースケース & ワークフロー](operations/audit-workflows.ja.md)
- [クラウドコスト分析](operations/cloud-cost-analysis.ja.md)
- [監査機構改善・構成管理](operations/harness-evolution.ja.md)

### :material-rocket-launch: セットアップガイド
- [監査対象プロジェクトへの導入・設定手順書](setup/target-project-guide.ja.md)
- [監査側初期構築手順書](setup/auditor-setup-guide.ja.md)
- [クラウド MCP サーバ設定ガイド](setup/cloud-mcp-server-guide.ja.md)

---

## ライセンス

MIT License — Copyright (c) 2026 @sun-flat-yamada (Youhei Yamada)
