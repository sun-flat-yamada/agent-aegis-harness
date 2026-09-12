---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "audit_rule"
id: "RULE-COPILOT-RULES-001"
title: "Aegis GitHub Copilot & Copilot CLI Governance Rules"
version: "1.1.0"
status: "active"
language: "ja"
canonical_ref: ".aegis/instructions/aegis-copilot-rules.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["github-copilot", "github-copilot-cli"]
  min_aah_version: "0.3.0"
tags: ["github-copilot", "github-copilot-cli", "vscode", "agent", "rules", "governance"]
---

# Aegis GitHub Copilot & Copilot CLI Governance Rules

本規約は、エディタ環境（VS Code / JetBrains 等の GitHub Copilot Chat, Inline, Edit）およびターミナル自律コーディング環境（GitHub Copilot CLI: 独立コマンド `copilot` および `gh copilot` 拡張）を利用する際に適用される共通監査ルールです。

## 1. ガバナンス基本規約の遵守
- 基本規約として [`.aegis/instructions/aegis-system-governance.md`](.aegis/instructions/aegis-system-governance.md) を厳格に遵守してください。

## 2. 自律エージェントセッションにおける 5W1H 意図開示
- Copilot CLI などの自律走行型エージェントループにおいて、ファイル編集やターミナルコマンド実行（Tool Call）を伴うアクションを行う前に、エージェントは「なぜその変更を行うのか (Why)」「どのファイルをどう変更するのか (What/How)」をコンテキスト上で明示開示してください。

## 3. シークレット保護と情報漏洩防止 (Zero Credential Leakage)
- 生成されたコードやチャットで提案されたコード、実行コマンド内に API キーやシークレットが含まれていないことを常に確認してください。
- 疑わしいトークンや認証情報は自動マスキング（Redaction）対象となります。

## 4. 実行境界と Sentinel ガバナンス (Sentinel & Wrapper Protection)
- Copilot CLI のセッションは原則として `aah wrap` の監視下で起動され、危険なシェルコマンド（システム破壊・不正通信など）は Sentinel によって即時インターセプト・遮断されます。

## 5. コミット・監査チェーンの整合性保持 (Git Chain Correlation)
- エージェントが作業を完了してコミットする際には、Aegis Git Hooks (`post-commit`) により、セッションハッシュとポリシーバンドルダイジェストが自動的にコミットメタデータに紐付けられます。

