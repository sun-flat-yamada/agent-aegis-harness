---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "DOC-PORTAL-INDEX"
title: "Agent Aegis Harness Documentation"
version: "1.0.0"
status: "active"
language: "en"
canonical_ref: "docs/index.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor"]
  min_aah_version: "0.1.0"
tags: ["portal", "overview", "quickstart"]
---

# Agent Aegis Harness

**Automated Evaluation & Governance Infrastructure for Software-AI**

---

## Welcome

Agent Aegis Harness (`aah`) is an end-to-end governance and observability harness for AI agents — including Google Antigravity, Claude Code, GitHub Copilot, and Cursor. It provides deterministic reproducibility, cryptographic audit immutability (Hash Chain), real-time 3-tiered defense, and offline self-refinement.

---

## Core Components

| Component | CLI Command | Description |
| :--- | :--- | :--- |
| **Execution Wrapper** | `aah wrap` | Transparent interception layer monitoring agent execution and 5W1H audit trails |
| **Sentinel (Evaluator)** | `aah sentinel` | Real-time 3-tiered defense (Tier 1 AST <10ms, Tier 2 lightweight model <100ms, Tier 3 LLM-Judge) with PII/Secret redactor |
| **Archivist (Notary)** | `aah archivist` | Policy bundle hasher (`policy_hash_digest`), Merkle Hash Chain verification, and deterministic reproducibility testing |
| **Recorder (Trail)** | `aah recorder` | 5W1H extractor with Dual-Stream Trail and OpenTelemetry exporter |
| **Refiner (Optimizer)** | `aah refiner` | Offline cluster analyzer generating rule/skill improvement Pull Requests |
| **Reporter** | `aah report` | Governance audit reporter (ISO/IEC 42001 & NIST AI RMF) |

---

## Quick Start

```bash
# Install
pip install agent-aegis-harness

# Initialize governance bundle
aah init

# Execute under Sentinel governance
aah wrap -- antigravity run

# Verify audit trail integrity
aah verify --log-file .aegis/logs/audit-trail.jsonl
```

---

## Documentation Guide

### :material-architecture: [Architecture & System Design](ARCHITECTURE.md)
Comprehensive system architecture, component interactions, and data flow diagrams.

### :material-gavel: Architecture Decision Records (ADR)
- [ADR-0001: Cryptographic Hash Chain for Audit Log Immutability](adr/0001-immutable-audit-log.md)
- [ADR-0002: Decoupling Real-time Auditing from Offline Self-Refinement](adr/0002-decoupled-refinement.md)
- [ADR-0003: Three-Tiered Documentation Structure by Persona](adr/0003-three-tiered-documentation.md)

### :material-cog: Operations & Workflows
- [Auditing Workflows & Forensic Operations](operations/audit-workflows.md)
- [Cloud Cost Analysis](operations/cloud-cost-analysis.md)
- [Harness Evolution & Version Management](operations/harness-evolution.md)

### :material-rocket-launch: Setup Guides
- [Target Project Setup & Tool Instrumentation](setup/target-project-guide.md)
- [Auditor & Governance Central Setup](setup/auditor-setup-guide.md)
- [Cloud MCP Server Configuration](setup/cloud-mcp-server-guide.md)

---

## License

MIT License — Copyright (c) 2026 @sun-flat-yamada (Youhei Yamada)
