---
name: Rule / Policy Proposal
about: Propose a new governance rule or optimization for Sentinel
title: "[RULE] "
labels: ["governance", "rules"]
assignees: ""
---

## Proposed Rule Summary
Describe the purpose and rationale of the proposed rule or policy modification.

## Target Category
- [ ] Security & Secret Redaction (`security-policy.yaml`)
- [ ] Context Drift & Compaction (`context-drift-policy.yaml`)
- [ ] Skill & Tool Compliance (`skill-compliance-policy.yaml`)
- [ ] Other

## Rule Specification Draft
```yaml
rule_id: "RULE-XXX-001"
name: "Proposed Rule Name"
severity: "HIGH" # CRITICAL | HIGH | MEDIUM | LOW
# Include pattern or criteria
```

## Expected Impact & Trade-offs
Describe how this rule prevents risks without causing undue friction for developers.
