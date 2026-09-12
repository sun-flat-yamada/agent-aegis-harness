---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "audit_rule"
id: "RULE-COPILOT-RULES-001"
title: "Aegis GitHub Copilot Governance Rules"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: ".aegis/instructions/aegis-copilot-rules.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["github-copilot"]
  min_aah_version: "0.3.0"
tags: ["github-copilot", "vscode", "rules", "governance"]
---

# Aegis GitHub Copilot Governance Rules

本規約は、VSCode GitHub Copilot (Chat, Inline, Edit) を利用する際に適用される個別監査ルールです。

## 1. ガバナンス規約の遵守
- 基本規約として [`.aegis/instructions/aegis-system-governance.md`](.aegis/instructions/aegis-system-governance.md) を遵守してください。

## 2. コミット前検証とシークレット防止
- 生成されたコードやチャットで提案されたコードに API キーやシークレットが含まれていないことを常に確認してください。
- コミット時には `git post-commit` により、本チャットセッションのハッシュが自動的にコミットメタデータに紐付けられます。
