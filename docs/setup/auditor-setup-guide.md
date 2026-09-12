---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "DOC-SETUP-AUDITOR-001"
title: "Auditor & Governance Central Setup Guide"
version: "1.0.0"
status: "active"
language: "en"
canonical_ref: "docs/setup/auditor-setup-guide.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.1.0"
tags: ["setup", "auditor", "central-governance", "opentelemetry", "worm"]
---

# Auditor & Governance Central Setup Guide

This guide describes how security, compliance, and governance teams establish central infrastructure to collect, verify, and monitor AI agent audit logs across enterprise repositories.

## 1. Central Governance Topology

```mermaid
flowchart LR
    subgraph TargetProjects ["Development Repositories"]
        P1["Project A (.aegis)"]
        P2["Project B (.aegis)"]
        PN["Project N (.aegis)"]
    end

    subgraph CentralInfrastructure ["Governance Infrastructure"]
        Registry["Central Policy Registry (Git)"]
        Collector["OpenTelemetry Collector"]
        SIEM["SIEM / Datadog / Azure Log Analytics"]
        WORM["Immutable WORM Storage (S3 / Azure Blob)"]
        AuditorCLI["Auditor Workstation (aah verify)"]
    end

    Registry -->|policy sync| TargetProjects
    TargetProjects -->|OTLP stream| Collector
    Collector --> SIEM
    Collector --> WORM
    WORM -->|audit verification| AuditorCLI
```

---

## 2. Infrastructure Setup Steps

### Step 1: Central Policy Registry
Maintain organization-wide governance rules in a centralized repository (`aegis-central-policies`). Individual repositories sync policies during CI builds or developer onboarding.

### Step 2: OpenTelemetry Ingestion Collector
Configure an OTel Collector to receive `AegisAuditEvent` telemetry via gRPC / HTTP (port 4317/4318) and route to central storage:
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
exporters:
  file:
    path: /var/log/aegis/central-audit.jsonl
service:
  pipelines:
    logs:
      receivers: [otlp]
      exporters: [file]
```

### Step 3: Immutable Storage (WORM Lock)
Enable compliance retention policies (such as AWS S3 Object Lock or Azure Blob Time-based Retention) to guarantee 3 to 10 years of immutable audit retention required by EU AI Act and SOC 2 Type II regulations.

---

## 3. Daily Governance Verification

Auditors verify log integrity using Archivist:
```bash
aah verify --log-file /path/to/central-audit.jsonl
```
This verifies:
- Unbroken cryptographic Hash Chain links ($H_i = \text{SHA256}(H_{i-1} + \text{Payload}_i)$)
- Matching `policy_hash_digest` against approved central policy versions
- Zero log tampering or missing events
