---
name: dev-change-lifecycle
description: "Governs the 5-stage document-driven development lifecycle: blueprint -> spec -> plan -> implementation -> walkthrough under .devs/changes/."
---

# Development Change Lifecycle Skill

本スキルは、ソフトウェア変更を安全・確実・決定論的に推進するための **5段階ドキュメント駆動型開発ライフサイクル** の標準仕様と運用手順を定めます。

```text
.devs/changes/YYYY-MM-DD_<change-name>/
├── blueprint.md       # 1. 構想企画 & ADR (なぜ作るか、何を狙うか)
├── spec.md            # 2. 要求分析 & 機能・データ仕様 (何を作るか)
├── plan.md            # 3. 開発計画 & WBS・テスト戦略 (どう進めるか)
├── implementation.md  # 4. Antigravity 実装詳細設計 (どう組むか)
└── walkthrough.md     # 5. 事後検証エビデンス (何が検証されたか)
```

---

## 1. ライフサイクル 5 大ドキュメント標準仕様

リポジトリ内のすべての Markdown は、先頭に以下の YAML Front-matter を付与します。

```yaml
---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "architecture_doc" # [system_prompt | audit_rule | skill_spec | architecture_doc | adr | guide]
id: "SPEC-XXX"
title: "Document Title"
version: "1.0.0"
status: "active" # [draft | active | deprecated | superseded]
language: "ja" # [en | ja]
canonical_ref: "docs/..."
hash_digest: "sha256:..."
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor"]
  min_aah_version: "0.1.0"
tags: ["lifecycle", "governance"]
author: "@user"
last_reviewed: "YYYY-MM-DD"
---
```

### Stage 1: `blueprint.md` (構想企画 & アーキテクチャブループリント)
- **目的**: 変更の動機、目的、設計思想、およびトレードオフ（ADR）を明文化する。
- **必須構成項目**:
  1. プロジェクト/変更基本メタデータ
  2. 意思決定背景・判断基準・トレードオフ (ADR)
  3. システムアーキテクチャ & コンポーネント役割 (Mermaid 図を含む)
  4. 初期プロトタイプ・主要スキーマドラフト
  5. ブートストラップ手順

### Stage 2: `spec.md` (要求分析 & 詳細仕様書)
- **目的**: `blueprint.md` の構想を、開発者が曖昧さなく実装可能な機能仕様・非機能要件・データ構造へ展開する。
- **必須構成項目**:
  1. システム全体像とドメインモデル
  2. データ構造 & スキーマ定義（JSON Schema / Pydantic 等）
  3. インターフェース仕様（CLI 引数、API エンドポイント、フック引数）
  4. セキュリティ、マスキング、コンテキストドリフト抑止要件
  5. 非機能要件（レスポンス遅延目標、耐改ざん性）

### Stage 3: `plan.md` (開発計画書 & WBS)
- **目的**: 仕様を実装するための工程計画、タスク分解、受け入れ基準、およびテスト戦略を定義する。
- **必須構成項目**:
  1. 開発方針・原則（決定論的再現性、多層防御等）
  2. マイルストーン & フェーズ計画（Gantt / タイムライン）
  3. タスク詳細 WBS（各モジュールごとの完了基準）
  4. テスト・検証戦略（単体テスト、改ざん検知テスト、E2Eテスト）
  5. リスク評価と緩和策

### Stage 4: `implementation.md` (Google Antigravity 実装設計書)
- **目的**: Google Antigravity 環境で動作する具体的なクラス設計、データモデル、フック連携アダプタ、およびコード生成順序を規定する。
- **必須構成項目**:
  1. Antigravity クラス設計 & 相互作用図（Mermaid classDiagram）
  2. ディレクトリ構成とモジュール配置
  3. コアデータモデル（Pydantic v2 定義）
  4. Google Antigravity ライフサイクルフック連携（`pre_turn`, `pre_tool_call_decide`, `on_compaction` 等）
  5. 署名・完全性検証アルゴリズム
  6. 実行・テストコマンド手順

### Stage 5: `walkthrough.md` (事後実証エビデンスレポート)
- **目的**: 実装完了後、変更内容とテスト検証結果をエビデンスとして記録・封印する。
- **必須構成項目**:
  1. 実施された変更一覧（変更ファイルとコミットリンク）
  2. 自動テスト結果（pytest 実行ログ、成否）
  3. CLI / ツール実機検証ログ（成否、判定結果）
  4. 画面・メディアエビデンス（必要な場合）

---

## 2. ディレクトリ命名・運用規約

1. **ディレクトリパス**: `.devs/changes/YYYY-MM-DD_<change-slug>/`
   - 例: `.devs/changes/2026-09-12_initial-create/`
   - 日付は ISO 形式（`YYYY-MM-DD`）。
   - change-slug は小文字英数字とハイフン。
2. **遷移の厳格性**:
   - 前のステージの文書が完成する前に次へ進まない。
   - `implementation.md` 完了後、必ず人間にレビュー承認を求め、承認を得るまでコード変更に着手してはならない。
