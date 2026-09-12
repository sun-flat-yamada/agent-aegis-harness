---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "adr"
id: "ADR-0001-JA"
title: "ADR-0001: 暗号学的 Hash Chain による監査ログ不変性の担保"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: "docs/adr/0001-immutable-audit-log.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.1.0"
tags: ["adr", "hash-chain", "immutability", "merkle-tree"]
---

# ADR-0001: 暗号学的 Hash Chain による監査ログ不変性の担保

## ステータス
承認 (Accepted)

## 文脈
AI によるコード生成・ツール実行ログは、法的・コンプライアンス要件（EU AI Act、SOC 2 Type II）を満たす必要があります。端末内のローカルログが開発者によって事後改ざん・削除可能であれば、監査証跡としての証拠価値を失います。

## 意思決定
すべての監査ログ（`audit-trail.jsonl` および `forensic-trail.jsonl`）に、直前行のハッシュを取り込んで自身を封印する Merkle Hash Chain 構造（$H_i = \text{SHA256}(H_{i-1} + \text{Payload}_i)$）を採用します。

## 結果・影響
- メリット: ログの1文字の改ざん、行の削除、順序の入替えを数学的に即座に検知可能。
- メリット: 外部ブロックチェーンやクラウドサービスへの依存ゼロでローカル完結。
- デメリット: 過去ログの修正が原理的に不可能となり、改ざん時は `aah verify` が直ちに停止。
