---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "audit_rule"
id: "RULE-SYSTEM-GOVERNANCE-001"
title: "Aegis Core System Governance Protocol"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: ".aegis/instructions/aegis-system-governance.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "windsurf", "aws-kiro", "cli"]
  min_aah_version: "0.3.0"
tags: ["governance", "5w1h", "security", "secrets", "compliance"]
---

# Aegis Core System Governance Protocol (組織全社監査規約)

本規約は、本プロジェクトにおいて AI 支援開発ツール（Claude Code, GitHub Copilot, AWS Kiro, Cursor 等）を利用する際に、エージェントおよび開発者が遵守すべき共通セキュリティ・監査要件を定めます。

## 1. 5W1H 監査説明責任
AI エージェントは、コードの新規生成・修正・コマンド実行を行う際、以下の 5W1H 要素を明確に意識して動作しなければなりません。
- **Who:** 操作者および AI モデル識別子
- **Why:** 変更・コマンド実行の背景、目的、および意図（Why）
- **What:** 具体的な変更対象ファイル、差分、または実行ツール引数
- **Where:** 対象リポジトリおよびブランチ
- **When:** 実行日時
- **How:** 実行プロセス（Sentinel 判定、検証結果）

## 2. 機微情報・シークレット取り扱いの絶対禁止
- API キー、パスワード、秘密鍵（`.env`, `*.pem`, `id_rsa`）、個人情報（PII）をコード中やプロンプト内に平文で記載・出力してはなりません。
- コミット前のステージング差分は必ずシークレットスキャンを通過しなければなりません。

## 3. 破壊的・危険コマンドの実行遮断
以下のコマンドパターンは、セキュリティポリシーにより実行が禁止されており、Sentinel によってブロックされます。
- ルートまたは広範囲の強制削除: `rm -rf /`, `rmdir /s /q C:\`
- データベースの無条件破壊: `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`
- 権限昇格・全開放: `chmod 777`
