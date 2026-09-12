---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "README-EN"
title: "Agent Aegis Harness (aah)"
version: "0.1.0"
status: "active"
language: "en"
canonical_ref: "README.md"
hash_digest: "sha256:pending"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "windsurf", "cli"]
  min_aah_version: "0.1.0"
tags: ["governance", "audit", "ai-agent", "opentelemetry", "harness"]
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
---

# Agent Aegis Harness (aah)

**Automated Evaluation & Governance Infrastructure for Software-AI**  
*An end-to-end technical harness to instrument, audit, and continuously evolve AI agent operations.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: >=3.10](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/sun.flat.yamada)

[日本語版ドキュメントはこちら (README.ja.md)](README.ja.md) | [Architecture Specification](docs/ARCHITECTURE.md)

---

## Overview

As autonomous AI agents (Google Antigravity, Claude Code, Cursor, GitHub Copilot) become standard in software engineering, maintaining security, policy compliance, and auditability is critical.

**Agent Aegis Harness (`aah`)** is a transparent governance harness that wraps around your AI developer tools. It provides deterministic reproducibility, cryptographic audit immutability (Hash Chain), real-time 3-tiered defense, and offline self-refinement.

---

## Core Components

- **`aah wrap`**: Transparent interception layer monitoring agent execution and 5W1H audit trails.
- **`aah sentinel`**: Real-time evaluator with 3-tiered defense (Tier 1 AST <10ms, Tier 2 lightweight model <100ms, Tier 3 LLM-Judge) and PII/Secret redactor.
- **`aah archivist`**: Policy bundle hasher (`policy_hash_digest`), Merkle Hash Chain verification, and deterministic reproducibility testing.
- **`aah recorder`**: 5W1H extractor with Dual-Stream Trail (`audit-trail.jsonl` and `forensic-trail.jsonl`) and OpenTelemetry exporter.
- **`aah refiner`**: Offline cluster analyzer generating rule/skill improvement Pull Requests.
- **`aah report`**: Governance audit reporter generating executive compliance reports (ISO/IEC 42001 & NIST AI RMF).

---

## Setup & Manual Configuration Requirements

Aegis is designed to operate with near-zero friction. Most setup tasks are completely automated by running `aah init`. However, certain operational modes and external platform integrations require **explicit manual administrative configuration**:

| Category | Automation Level | Manual Action Required | Detailed Guide |
| :--- | :--- | :--- | :--- |
| **Target Project Instrumentation** | **Fully Automated** | None for standard use (`aah init`). When customizing rules or instructions, keep injection pointers (`<!-- AEGIS-AUDIT-INJECTION -->`) intact. | [Target Project Guide](docs/setup/target-project-guide.md) |
| **GitHub Pages Documentation** | **One-Time Manual** | In GitHub repository **Settings → Pages**, change Source to **GitHub Actions**. | [GitHub Pages Setup Guide](docs/setup/github-pages-setup.md) |
| **Central Auditor Infrastructure** | **Manual Setup** | Deploy OpenTelemetry Collector, configure cloud WORM storage lock (S3 Object Lock / Azure Immutable Blob), and sync central policies. | [Auditor Setup Guide](docs/setup/auditor-setup-guide.md) |
| **Cloud MCP Security Gateway** | **Infrastructure Setup** | Deploy Azure/AWS infrastructure via Terraform, configure Entra ID authentication, and register endpoint in developer IDE settings. | [Cloud MCP Server Guide](docs/setup/cloud-mcp-server-guide.md) |

---

## Usage by Persona

Aegis provides tailored workflows depending on your role. Detailed guides are available under `docs/`.

### 1. For Target Project Developers
Instrument your development repository to monitor and guard agent operations with zero friction:

```bash
# Install development dependency
pip install agent-aegis-harness

# Initialize Aegis governance bundle (.aegis/, .hooks/, .skills/)
aah init

# Execute commands under Sentinel governance
aah wrap -- antigravity run
```
📖 **Detailed Guide:** [Target Project Setup & Tool Instrumentation Guide](docs/setup/target-project-guide.md)

---

### 2. For Auditors & Security Teams
Establish organization-wide central governance, automated CI gates, and cryptographic verification:

```bash
# Verify policy bundle integrity and run instant checks
aah check

# Automated CI gate (exits with code 1 on violations)
aah check --strict

# Cryptographically verify audit trail integrity (Merkle Hash Chain)
aah verify --log-file .aegis/logs/audit-trail.jsonl

# Generate governance compliance report
aah report -o .aegis/reports/weekly-audit.md
```
📖 **Detailed Guides:**
- [Auditor & Governance Central Setup Guide](docs/setup/auditor-setup-guide.md)
- [Auditing Workflows & Forensic Operations Guide](docs/operations/audit-workflows.md)

---

### 3. For Harness Engineers & Policy Curators
Evolve audit policies, schemas, and AI skills safely without breaking backward compatibility:

```bash
# Run offline cluster analysis on historical audit logs
aah refine

# Generate automated policy improvement Pull Request proposal
aah refine --propose-pr
```
📖 **Detailed Guide:** [Harness Evolution & Version Consistency Management Guide](docs/operations/harness-evolution.md)

---

## Architecture Decision Records (ADR)
- [ADR-0001: Cryptographic Hash Chain for Audit Log Immutability](docs/adr/0001-immutable-audit-log.md)
- [ADR-0002: Decoupling Real-time Auditing from Offline Self-Refinement](docs/adr/0002-decoupled-refinement.md)
- [ADR-0003: Three-Tiered Documentation Structure by Persona](docs/adr/0003-three-tiered-documentation.md)

---

## 🤝 Contribution & Support

Contributions are welcome! If you find this tool useful, please consider supporting its development.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/sun.flat.yamada)

---

## License

MIT License - Copyright (c) 2026 @sun-flat-yamada (Youhei Yamada)
