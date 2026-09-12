---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "adr"
id: "ADR-0002-JA"
title: "ADR-0002: 監査実行と自己改善ループの疎結合分離"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: "docs/adr/0002-decoupled-refinement.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.1.0"
tags: ["adr", "refinement", "decoupling", "reproducibility"]
---

# ADR-0002: 監査実行と自己改善ループの疎結合分離

## ステータス
承認 (Accepted)

## 文脈
エージェントが自律的にルールを学習・更新する際、監査実行と自己改善を同一ループでリアルタイム連動させると、「ある操作がどのバージョンのルールで判定されたか」が不透明になり、過去の監査判定を同一コードとデータで再現する「決定論的再現性」が崩壊します。

## 意思決定
監査（Sentinel / Archivist）と自己改善（Refiner）を完全に分離します。監査実行時はその瞬間の `policy_hash_digest` を固定してログを封印し、Refiner はオフラインバッチとして稼働して、人間の承認を要する Pull Request としてポリシー改善を提案します。

## 結果・影響
- メリット: 過去の任意の時点における判定を100%再現可能な監査証跡の確保。
- メリット: ガバナンス改定が Git 履歴として透明に記録・レビュー可能。
- デメリット: ルールの即時自動変更は行われず、PR のマージ手続きが必要。
