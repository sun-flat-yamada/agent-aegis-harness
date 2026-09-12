---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "adr"
id: "ADR-0003-JA"
title: "ADR-0003: 利用者ペルソナ別 3 分類ドキュメント階層の採用"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: "docs/adr/0003-three-tiered-documentation.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.1.0"
tags: ["adr", "documentation", "personas", "architecture"]
---

# ADR-0003: 利用者ペルソナ別 3 分類ドキュメント階層の採用

## ステータス
承認 (Accepted)

## 文脈
初期の README では、開発者向けの導入手順、監査役・セキュリティチーム向けの初期構築・検証手順、およびハーネス運用者向けのルール改善手順が単一ページに混在し、開発者の導入摩擦を高めると同時に専門的な監査要件の記述が不足していました。

## 意思決定
すべてのドキュメント体系を 3 つのペルソナ別ワークフローに整理・階層化します：
1. **被監査プロジェクト開発者 (`docs/setup/target-project-guide.ja.md`)**: 高速セットアップ、フック連携、日常業務の邪魔をしない設計。
2. **監査・ガバナンス担当者 (`docs/setup/auditor-setup-guide.ja.md`, `docs/operations/audit-workflows.ja.md`)**: 中央集約、WORM 不変ストレージ、改ざん検証、インシデント調査。
3. **ハーネス運用・改善エンジニア (`docs/operations/harness-evolution.ja.md`)**: ルール改善、スキーマ SemVer 管理、決定論的再現テスト。
ルートの `README.ja.md` はこれら 3 分類へのクイックリファレンスとして端的に整理します。

## 結果・影響
- メリット: 開発者は 2 分で迷わずセットアップを完了可能。
- メリット: セキュリティ・監査チームが必要な技術仕様に即座に到達可能。
- デメリット: 英語正本と日本語版の 1:1 対称性を維持する保守コストが発生。
