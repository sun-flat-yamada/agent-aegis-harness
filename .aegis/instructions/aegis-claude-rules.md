---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "audit_rule"
id: "RULE-CLAUDE-RULES-001"
title: "Aegis Claude Code Governance Rules"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: ".aegis/instructions/aegis-claude-rules.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["claude-code"]
  min_aah_version: "0.3.0"
tags: ["claude-code", "mcp", "rules", "governance"]
---

# Aegis Claude Code Governance Rules

本規約は、Claude Code CLI が本リポジトリ内で自律開発を実行する際に適用される個別監査ルールです。

## 1. ガバナンス規約の遵守
- 基本規約として [`.aegis/instructions/aegis-system-governance.md`](.aegis/instructions/aegis-system-governance.md) を遵守してください。

## 2. 思考過程（Reasoning & Intent）の明記
- ユーザーからの指示を受けてツール（View, Edit, Bash）を呼び出す前に、何のためにどのような変更を行うのか（Why & What）を簡潔に思考ブロックまたはメッセージに出力してください。

## 3. Aegis MCP Security Gateway の利用
- 機微なシェル操作やファイル編集を行う際は、プロジェクトに登録された `aegis-security` MCP ツールを優先して経由してください。Sentinel の検閲によりブロックされた場合は、代替手段を検討するか人間に確認を求めてください。
