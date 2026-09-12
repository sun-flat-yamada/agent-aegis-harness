---
name: ルール・ポリシー提案 (Rule Proposal)
about: Sentinel 向けの新規監査ルールまたは既存ルールの最適化を提案する
title: "[RULE] "
labels: ["governance", "rules"]
assignees: ""
---

## 提案の概要
提案するルールまたはポリシー改定の目的と背景・動機を記述してください。

## 対象カテゴリ
- [ ] セキュリティ & シークレットマスキング (`security-policy.yaml`)
- [ ] コンテキストドリフト & 要約逸脱抑止 (`context-drift-policy.yaml`)
- [ ] スキル & ツール利用コンプライアンス (`skill-compliance-policy.yaml`)
- [ ] その他

## ルール仕様ドラフト
```yaml
rule_id: "RULE-XXX-001"
name: "提案ルール名"
severity: "HIGH" # CRITICAL | HIGH | MEDIUM | LOW
# パターンや判定基準を記載
```

## 想定される効果とトレードオフ
開発者の日常業務への摩擦（False Positive）を最小限に抑えつつ、どのようなリスクを排除できるかを記述してください。
