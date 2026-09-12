---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "README-JA"
title: "Agent Aegis Harness (aah) - 日本語版概要"
version: "0.1.0"
status: "active"
language: "ja"
canonical_ref: "README.md"
hash_digest: "sha256:pending"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "windsurf", "cli"]
  min_aah_version: "0.1.0"
tags: ["governance", "audit", "ai-agent", "opentelemetry", "harness"]
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
---

# Agent Aegis Harness (aah)

**ソフトウェア開発AIのための自動評価・ガバナンス基盤**  
*AIエージェントの挙動を計装・監査し、継続的に改善するための包括的開発ハーネス*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: >=3.10](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/sun.flat.yamada)

[English Version (README.md)](README.md) | [アーキテクチャ設計書](docs/ARCHITECTURE.ja.md)

---

## 概要

自律型AIエージェント（Google Antigravity, Claude Code, Cursor, GitHub Copilot）の開発現場への普及に伴い、セキュリティ侵害の防止、ポリシー遵守、そして過去の操作の再現性・監査可能性の担保が必須となっています。

**Agent Aegis Harness (`aah`)** は、AIツール群に装着する「馬具（Harness）」として機能する共通ガバナンス基盤です。ルールハッシュによる決定論的再現性、Hash Chain による改ざん防止、3段階の多層防御 Sentinel、および監査と疎結合な自己改善ループを提供します。

---

## コアコンポーネント

- **`aah wrap`**: AIエージェントの透過実行ラッパー。5W1H 監査ログを自動記録。
- **`aah sentinel` (監査員)**: 3段階多層防御（Tier 1 AST <10ms、Tier 2 小型モデル <100ms、Tier 3 LLM-Judge）および PII/シークレット即時マスキング。
- **`aah archivist` (書記・台帳管理)**: ルール群の統合ハッシュ算出（`policy_hash_digest`）、ログ改ざん検証、監査再現性テスト。
- **`aah recorder` (証跡記録)**: デュアルストリーム監査ログ（軽量 `audit-trail.jsonl` と完全フォレンジック `forensic-trail.jsonl`）の出力および OpenTelemetry 転送。
- **`aah refiner` (改善・最適化)**: 監査履歴をオフライン分析し、ルール・スキルの改善 PR を自動生成。
- **`aah report` (監査レポート)**: ISO/IEC 42001 & NIST AI RMF 準拠のガバナンス要約レポートを生成。

---

## セットアップと手動設定要件（自動化と手動設定の切り分け）

Aegis は開発者の業務摩擦を最小化するよう設計されており、通常の開発プロジェクト導入は `aah init` の実行のみで**全自動**で完了します。ただし、外部プラットフォーム連携や全社統制インフラの構築など、特定の利用シナリオでは**手動での初期設定**が必要です。

| 分類 | 自動化レベル | 必要な手動設定・アクション | 詳細ガイド |
| :--- | :--- | :--- | :--- |
| **監査対象プロジェクトへの導入** | **全自動** | 通常利用は `aah init` のみで完了。独自規約を追加する場合はインジェクションポインタ（`<!-- AEGIS-AUDIT-INJECTION -->`）を維持。 | [監査対象プロジェクト導入ガイド](docs/setup/target-project-guide.ja.md) |
| **GitHub Pages ドキュメント公開** | **初回手動設定** | GitHub リポジトリの **Settings → Pages** で Source を **GitHub Actions** に変更（初回1回のみ）。 | [GitHub Pages 公開設定手順書](docs/setup/github-pages-setup.ja.md) |
| **監査側・中央統制基盤の構築** | **手動インフラ構築** | OpenTelemetry Collector の配備、クラウド不変ストレージ（WORM ロック）の有効化、中央ポリシーリポジトリの同期。 | [監査側初期構築手順書](docs/setup/auditor-setup-guide.ja.md) |
| **Cloud MCP セキュリティゲートウェイ** | **手動インフラ構築** | Terraform によるクラウド基盤（Azure/AWS）のプロビジョニング、認証設定、およびクライアント端末の MCP 設定。 | [クラウド MCP サーバ設定ガイド](docs/setup/cloud-mcp-server-guide.ja.md) |

---

## 使い方 (Usage - 利用者ペルソナ別)

利用者の役割に合わせて、以下の3つのワークフローを提供しています。詳細な仕様・手順は `docs/` 配下のドキュメントを参照してください。

### 1. 監査対象プロジェクトへの導入・設定 (For Target Projects)
AI エージェントを利用するリポジトリに Harness を装着し、リアルタイム監査と証跡記録を有効化します。

```bash
# 依存関係のインストール
pip install agent-aegis-harness

# リポジトリに Aegis 設定 (.aegis/) と Hooks (.hooks/) を初期化
aah init

# AI エージェントコマンドを Sentinel 統制下で実行・記録
aah wrap -- antigravity run
```
📖 **詳細ガイド:** [監査対象プロジェクトへの導入・設定手順書](docs/setup/target-project-guide.ja.md)

---

### 2. 監査側の初期構築 & 監査実施 (For Auditors & Security Teams)
セキュリティ・ガバナンスチームが監査基盤を整備し、定常監査、改ざん検証、インシデント調査を実施します。

```bash
# 【健全性確認】中央ポリシーの同期・監査環境の整合性チェック
aah check

# 【監査実施: CI/CD】コミット前・CI での即時判定 (違反時は exit 1)
aah check --strict

# 【監査実施: 改ざん検証】監査ログの暗号学的改ざん検知 (Merkle Hash Chain 検証)
aah verify --log-file .aegis/logs/audit-trail.jsonl

# 【監査実施: レポーティング】ISO 42001 準拠の週次ガバナンスレポート出力
aah report -o .aegis/reports/weekly-audit.md
```
📖 **詳細ガイド:** 
- [監査側初期構築手順書](docs/setup/auditor-setup-guide.ja.md)
- [監査実施ユースケース & ワークフロー例](docs/operations/audit-workflows.ja.md)

---

### 3. 監査機構の改善 & 構成管理 (For Harness Evolution)
蓄積されたログからルールやスキルを自己改善し、スキーマやポリシーのバージョン整合性を維持します。

```bash
# オフラインログ分析による改善候補のクラスタリング抽出
aah refine

# 改善パッチの自動ブランチ作成 & Pull Request 起票
aah refine --propose-pr
```
📖 **詳細ガイド:** [監査機構改善・構成管理・バージョン整合管理手順書](docs/operations/harness-evolution.ja.md)

---

## 設計意思決定記録 (ADR)
- [ADR-0001: 暗号学的 Hash Chain による監査ログ不変性の担保](docs/adr/0001-immutable-audit-log.ja.md)
- [ADR-0002: 監査実行と自己改善ループの疎結合分離](docs/adr/0002-decoupled-refinement.ja.md)
- [ADR-0003: 利用者ペルソナ別 3 分類ドキュメント階層の採用](docs/adr/0003-three-tiered-documentation.ja.md)

---

## 🤝 Contribution & Support

Contributions are welcome! If you find this tool useful, please consider supporting its development.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/sun.flat.yamada)

---

## ライセンス

MIT License - Copyright (c) 2026 @sun-flat-yamada (Youhei Yamada)
