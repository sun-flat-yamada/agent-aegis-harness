---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "DOC-OPS-WORKFLOWS-001"
title: "Auditing Workflows & Forensic Operations Guide"
version: "1.0.0"
status: "active"
language: "en"
canonical_ref: "docs/operations/audit-workflows.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.1.0"
tags: ["operations", "audit", "workflows", "forensics", "ci-gate"]
---

# Auditing Workflows & Forensic Operations Guide

This guide details everyday operational workflows for security teams and auditors conducting real-time evaluations, automated CI gates, cryptographic verification, and forensic investigations.

## 1. Audit Operations Matrix

| Workflow | Trigger | Objective | Primary Command |
| :--- | :--- | :--- | :--- |
| **UC-1: CI/CD Quality Gate** | PR or commit push | Block unapproved commands, leaks, and drift | `aah check --strict` |
| **UC-2: Integrity Verification** | Daily / weekly batch | Verify Hash Chain mathematical integrity | `aah verify --log-file <path>` |
| **UC-3: Incident Deep-Dive** | Security incident | Inspect complete reasoning & raw diffs | Grep trace_id in `forensic-trail.jsonl` |
| **UC-4: Governance Reporting** | Weekly / monthly | Generate compliance summary (ISO 42001) | `aah report -o report.md` |

---

## 2. Operational Workflows

### UC-1: Automated CI/CD Gate
In GitHub Actions or CI pipelines, execute:
```bash
aah check --strict
```
- **Exit Code 0**: All policies pass cleanly.
- **Exit Code 1**: Warning or BLOCK violation detected (e.g. unredacted secrets or dangerous command). Pull Request merge is prevented automatically.

### UC-2: Hash Chain Tampering Detection
Auditors verify audit trails locally or from WORM storage:
```bash
aah verify --log-file .aegis/logs/audit-trail.jsonl
```
If any byte was altered or deleted, Archivist immediately pinpoints the exact corrupted block and exits with code 2.

### UC-3: Incident Forensics (5W1H Deep Dive)
When investigating a suspicious event:
1. Identify the offending `trace_id` from `audit-trail.jsonl`.
2. Query `forensic-trail.jsonl` for full reasoning details:
   ```bash
   grep "<trace_id>" .aegis/logs/forensic-trail.jsonl | jq .
   ```
3. Correlate with the recorded `git_commit` and verify the exact prompt that initiated the operation.

### UC-4: ISO 42001 Executive Reporting
Generate a structured governance summary:
```bash
aah report -o .aegis/reports/weekly-audit.md
```
Outputs tracked events, pass/fail counts, and cryptographic seal verification status.
