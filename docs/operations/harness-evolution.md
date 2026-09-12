---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "DOC-OPS-EVOLUTION-001"
title: "Harness Evolution & Version Consistency Management Guide"
version: "1.0.0"
status: "active"
language: "en"
canonical_ref: "docs/operations/harness-evolution.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.1.0"
tags: ["evolution", "refinement", "semver", "reproducibility", "policy-hasher"]
---

# Harness Evolution & Version Consistency Management Guide

This guide governs how policies, schemas, and AI skills evolve over time while preserving backward compatibility and deterministic historical reproducibility.

## 1. Principles of Continuous Governance Evolution

```mermaid
flowchart TD
    PastLogs["Historical Audit Logs (3-10 Years)"] --> Refiner["aah refine (Offline Cluster Analysis)"]
    Refiner --> Proposal["Patch Proposal (PR)"]
    Proposal --> HumanReview["Security Team Approval"]
    HumanReview --> PolicyCommit["Git Commit (.aegis/rules)"]
    PolicyCommit --> NewDigest["New policy_hash_digest Sealed"]
```

1. **Decoupled Refinement**: Policies are updated via deliberate Human-in-the-Loop Git Pull Requests, never during real-time auditing.
2. **Canonical Policy Digest**: Any change to `.aegis/rules/` or `.skills/` automatically recalculates a new deterministic `policy_hash_digest`.
3. **Decodability Guarantee**: Historical logs recorded years ago must always decode and verify successfully against schema specifications.

---

## 2. Schema SemVer & Dual-Reading Protocol

Audit schemas (`.aegis/schemas/audit-event.schema.json`) follow strict Semantic Versioning:
- **Patch (`x.y.Z`)**: Field descriptions, formatting examples.
- **Minor (`x.Y.z`)**: Adding optional fields (e.g. `environment.ide_version`). Old logs remain fully compliant without breaking.
- **Major (`X.y.z`)**: Breaking field alterations. Aegis adopts a Multi-Schema coexistence strategy (`audit-event.v2.schema.json`), allowing verifiers to select the appropriate parser based on the event's schema reference.

---

## 3. Policy Update Procedure

1. Run Refiner on historical logs:
   ```bash
   aah refine --propose-pr
   ```
2. Inspect recommendations:
   - Identify unwhitelisted tools repeatedly requested by developers.
   - Adjust drift threshold if false-positive warnings exceed acceptable rates.
3. Apply changes and verify:
   ```bash
   pytest -v tests/
   aah check
   ```
4. Submit PR for security review and merge into the central policy repository.
