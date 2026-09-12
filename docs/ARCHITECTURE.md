---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "architecture_doc"
id: "DOC-ARCH-001"
title: "Agent Aegis Harness Architecture & System Design"
version: "1.0.0"
status: "active"
language: "en"
canonical_ref: "docs/ARCHITECTURE.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.1.0"
tags: ["architecture", "sentinel", "archivist", "recorder", "refiner"]
---

# Agent Aegis Harness Architecture & System Design

## 1. System Vision
Agent Aegis Harness (`aah`) provides an end-to-end governance and observability harness for AI agents (Google Antigravity, Claude Code, GitHub Copilot, Cursor, etc.). It acts as transparent equipment attached to developer workflows, providing deterministic auditability, cryptographic immutability, multi-tiered guardrails, and offline self-refinement.

```mermaid
flowchart TD
    subgraph HarnessExecution ["1. Execution & Interception Layer"]
        Prompt["Developer Prompt / CI Trigger"] --> Wrapper["aah wrap / Antigravity Hooks"]
        Wrapper --> Redactor["Sensitive Redactor (PII/Secret)"]
        Redactor --> Agent["AI Developer Agent"]
    end

    subgraph GovernanceLayer ["2. Sentinel & Archivist Governance"]
        Agent --> Sentinel["Sentinel Judge (Tier 1 AST, Tier 2 Model)"]
        Sentinel --> Verdict{"Verdict: PASS / WARN / BLOCK"}
        Archivist["Archivist (Policy Hasher & Hash Chain)"] -.->|Deterministic Hash| Sentinel
    end

    subgraph AuditTrailLayer ["3. Dual-Stream Trail & Telemetry"]
        Verdict --> Recorder["Aegis Recorder (5W1H Tracing)"]
        Recorder --> CompactLog["audit-trail.jsonl (Compact Ledger)"]
        Recorder --> ForensicLog["forensic-trail.jsonl (Deep Forensics)"]
        Recorder --> OTel["OpenTelemetry / Central SIEM"]
        Archivist -->|Hash Chain Seal| CompactLog
        Archivist -->|Hash Chain Seal| ForensicLog
    end

    subgraph OptimizationLayer ["4. Refiner (Offline Self-Improvement)"]
        CompactLog -.->|Offline Batch| Refiner["Cluster Analyzer & Patch Proposer"]
        Refiner --> PR["Rules / Skills Improvement Pull Request"]
    end
```

## 2. Core Subsystems

### 2.1 Sentinel (Real-time Guardrail & Judge)
- **Tier 1 (<10ms)**: Fast in-process AST and regex filtering detecting destructive shell commands (`rm -rf /`, formatting, recursive disk deletion) and policy violations.
- **Sensitive Redactor**: Pre-execution masking of API keys (OpenAI, GitHub, AWS), generic secret tokens, IPv4 addresses, and email addresses.

### 2.2 Archivist (Cryptographic Proof & Reproducibility)
- **Policy Hasher**: Computes a canonical SHA-256 digest (`policy_hash_digest`) across all active policies (`.aegis/rules/`) and skills (`.skills/`).
- **Hash Chain Manager**: Blockchain-style cryptographic linking of audit records ($H_i = \text{SHA256}(H_{i-1} + \text{Payload}_i)$). Detects any tampering, deletion, or reordering.

### 2.3 Recorder (5W1H Dual-Stream Tracing)
- **Compact Trail (`audit-trail.jsonl`)**: Lightweight summary trail for rapid verification and dashboard reporting.
- **Forensic Trail (`forensic-trail.jsonl`)**: Full deep-dive trail preserving complete prompt contexts, reasoning traces, and tool arguments.
- **Independent Merkle Linking**: Both trails maintain independent cryptographic hash chains to ensure complete mathematical integrity.

### 2.4 Refiner (Offline Self-Improvement)
- **Decoupled Architecture**: Refinement runs purely offline to maintain deterministic historical reproducibility.
- **Cluster Analyzer**: Aggregates recurring block patterns, unwhitelisted tools, and drift occurrences.
- **Patch Proposer**: Generates recommended policy adjustments and automated Pull Request proposals.
