---
description: "Rules enforcing the 5-stage document-driven development lifecycle (.devs/changes/ -> blueprint -> spec/plan -> implementation -> review -> walkthrough)."
globs: ["**/*"]
always_on: true
---

# Development Lifecycle & Governance Rules

本プロジェクト（agent-aegis-harness）におけるすべての機能開発、仕様変更、大規模リファクタリングは、以下の「5段階開発ライフサイクル」を遵守しなければなりません。

## 1. 原則: 直書き変更の禁止 (No Direct Unplanned Changes)
- 計画外のアドホックなコード直接変更を行ってはならない。
- すべての変更は `.devs/changes/YYYY-MM-DD_<issue-name>/` ディレクトリを起点とする。

## 2. 必須遷移プロセス
1. **構想企画**: `blueprint.md` の作成（動機、ADR、アーキテクチャ）
2. **分析・展開**: `spec.md`（要求・データ仕様）および `plan.md`（マイルストーン・テスト戦略）の作成
3. **実装設計**: `implementation.md`（Antigravity クラス設計・フック・コマンド）の作成
4. **人間承認 (Human-in-the-Loop)**: `implementation_plan.md` / `ask_question` による人間レビューの獲得
5. **実装・検証**: テスト実行による確認後、`walkthrough.md` にエビデンスを封印

## 3. スキル参照義務
エージェントは変更着手時に以下のスキルを参照すること：
- [dev-change-lifecycle](file:///.agents/skills/dev-change-lifecycle/SKILL.md)
- [antigravity-two-phase-governance](file:///.agents/skills/antigravity-two-phase-governance/SKILL.md)
