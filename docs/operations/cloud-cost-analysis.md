---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "DOC-OPS-COST-001-EN"
title: "Agent Aegis Harness Cloud Operations Estimated Cost Analysis Report"
version: "1.0.0"
status: "active"
language: "en"
canonical_ref: "docs/operations/cloud-cost-analysis.ja.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.3.0"
tags: ["cost-analysis", "cloud-mcp", "azure", "finops", "governance"]
---

# Agent Aegis Harness Cloud Operations Estimated Cost Analysis Report

## 1. Executive Summary

This report provides a comprehensive cost estimation and analysis for operating the central governance platform of Agent Aegis Harness (`aah`)—specifically the **Aegis Cloud MCP Security Gateway** and the **Enterprise Central Audit & WORM Storage Infrastructure**—in a public cloud environment (Microsoft Azure East Japan: `japaneast`).

Based on operational metrics including the number of active projects and participating developers, three operational profiles are evaluated: **Small (PoC / Team)**, **Medium (Department / Business Unit)**, and **Large (Enterprise-wide Platform)**. For each profile, detailed cost breakdowns, annual expenses, and per-developer monthly costs are calculated.

All unit rates, formulas, and quotas utilized in this model have been validated against official Microsoft Azure pricing documentation and the public REST endpoint **Azure Retail Prices API**, including HTTP 200 availability verification and short quote grounding.

### Sizing Profile Comparison Summary

*Exchange rate assumption: **1 USD = 150 JPY**.*

| Scale Profile | Active Projects | Active Developers | Monthly Audit Events | Monthly Data Ingestion | Monthly Estimated Cost (USD) | Monthly Estimated Cost (JPY) | Annual Estimated Cost (JPY) | Monthly Cost per Developer |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Small (PoC / Team)** | 3 PJ | 15 devs | 30,000 req/mo | 0.48 GB/mo | **\$34.73 / mo** | **~¥5,210** | **~¥62,516** | **~¥347 / dev-mo** |
| **Medium (Department)** | 20 PJ | 100 devs | 200,000 req/mo | 3.20 GB/mo | **\$58.17 / mo** | **~¥8,725** | **~¥104,700** | **~¥87 / dev-mo** |
| **Large (Enterprise)** | 100 PJ | 1,000 devs | 2,000,000 req/mo | 32.00 GB/mo | **\$225.91 / mo** | **~¥33,886** | **~¥406,629** | **~¥34 / dev-mo** |

> [!TIP]
> **Key Finding**:
> Even at an enterprise scale of 100 projects and 1,000 developers, the total infrastructure cost remains modest at **~¥33,886/month (~¥406,629/year)**, equating to merely **~¥34/developer/month**. Applying the dual-stream routing optimization outlined in Section 7 further reduces enterprise monthly costs to **~¥18,856/month (~¥19/developer/month)**.

---

## 2. Architecture & Cost Component Breakdown

The architecture follows the IaC definition in [`infra/azure/main.tf`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/infra/azure/main.tf) and the deployment guide in [`docs/setup/cloud-mcp-server-guide.ja.md`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/docs/setup/cloud-mcp-server-guide.ja.md).

```mermaid
flowchart TD
    subgraph Clients ["Client Tier (Developer Workstations / Projects)"]
        IDE["AI Tools (Antigravity, Claude Code, Cursor)"]
    end

    subgraph AzureRegion ["Microsoft Azure (japaneast)"]
        subgraph IngressSecurity ["1. Container Execution & Inspection"]
            ACA["Azure Container Apps (Standard)<br/>aegis-mcp-gateway"]
            KV["Azure Key Vault (Standard)<br/>Auth Tokens & Cryptographic Keys"]
        end

        subgraph IngestionStream ["2. High-Throughput Streaming"]
            AEH["Azure Event Hubs (Standard)<br/>Throughput Units (TU)"]
        end

        subgraph StorageAnalytics ["3. Immutable Storage & Analytics"]
            BLOB["Azure Blob Storage (Cool GRS)<br/>WORM Policy (3-Year Immutability)"]
            LA["Azure Log Analytics Workspace<br/>Hot Search / Microsoft Sentinel"]
        end
    end

    IDE -->|HTTPS / SSE (Bearer Token)| ACA
    ACA -.->|Token Validation| KV
    ACA -->|Audit Stream (5W1H)| AEH
    AEH -->|Capture / Batch Write| BLOB
    AEH -->|Hot Stream Feed| LA
```

### Components Evaluated
1. **Azure Container Apps (Security Gateway)**: Lightweight Python/FastAPI container hosting the in-process Sentinel judge (ALLOW/BLOCK). Billed via Consumption plan based on vCPU-seconds, GiB-seconds, and request count.
2. **Azure Event Hubs (Ingestion Plane)**: High-throughput buffer for incoming 5W1H audit records. Billed by Throughput Units (TU) and ingress events.
3. **Azure Blob Storage (WORM Storage Tier)**: Immutable WORM storage for `audit-trail.jsonl` and `forensic-trail.jsonl` with a 3-year (1,095-day) retention policy. Utilizes Cool GRS (Geo-Redundant Storage).
4. **Azure Log Analytics Workspace (Hot Search Tier)**: Ingestion and 30-day hot search for incident investigation and Microsoft Sentinel KQL queries.
5. **Azure Key Vault & Egress Bandwidth**: Token authentication and internet egress (first 100 GB/month free).

---

## 3. Unit Pricing, Official Sources, and Grounding Verification

To guarantee rigorous financial accountability, every rate has been retrieved and verified from official Microsoft documentation and the live **Azure Retail Prices API** (`japaneast`).

### 3.1 Official Sources and Short Quotes

| Component | Official URL | Document Short Quote |
| :--- | :--- | :--- |
| **Azure Container Apps** | [Container Apps Pricing](https://azure.microsoft.com/en-us/pricing/details/container-apps/) | *"Azure Container Apps consumption plan is billed based on per-second resource allocation and requests. The first 180,000 vCPU-seconds, 360,000 GiB-seconds, and 2 million requests per subscription per month are free. Beyond that, you pay for what you use on a per second basis based on the number of vCPU-s and GiB-s your applications are allocated."* |
| **Azure Event Hubs** | [Event Hubs Pricing](https://azure.microsoft.com/en-us/pricing/details/event-hubs/) | *"/hour per Throughput Unit"* / *"Ingress events"* (1 TU provides 1 MB/s ingress or 1,000 events/s) |
| **Azure Blob Storage** | [Blob Storage Pricing](https://azure.microsoft.com/en-us/pricing/details/storage/blobs/) | *"The Cool and Archive tiers are for cool or cold data with pricing optimized for lowest GB storage prices."* / *"Any blob that is moved to the Cool tier is subject to a Cool tier early deletion period of 30 days."* |
| **Azure Monitor / Log Analytics** | [Azure Monitor Pricing](https://azure.microsoft.com/en-us/pricing/details/monitor/) | *"Azure Monitor includes functionality for the collection and analysis of log data (billed by data ingestion, retention, and export)... Features of Azure Monitor that are automatically enabled such as collection of standard metrics and activity logs are provided at no cost."* |
| **Azure Key Vault** | [Key Vault Pricing](https://azure.microsoft.com/en-us/pricing/details/key-vault/) | *"Safeguard and maintain control of keys and other secrets"* |

### 3.2 Azure Retail Prices API Verification (`japaneast`)

- **API Endpoint**: `https://prices.azure.com/api/retail/prices`
- **Verification Date**: 2026-09-12
- **Region**: `japaneast`
- **Currency**: USD

| Service Name | SKU Name | Meter Name | Unit Price (USD) | Unit of Measure | Validation Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Azure Container Apps** | Standard | Standard vCPU Active Usage | **\$0.00002400** | 1 Second | Verified |
| | Standard | Standard Memory Active Usage | **\$0.00000300** | 1 GiB Second | Verified |
| | Standard | Standard vCPU Idle Usage | **\$0.00000300** | 1 Second | Verified |
| | Standard | Standard Memory Idle Usage | **\$0.00000300** | 1 GiB Second | Verified |
| | Standard | Standard Requests | **\$0.40000000** | 1M Requests | Verified |
| **Azure Event Hubs** | Standard | Standard Throughput Unit | **\$0.03000000** | 1 Hour (\$21.60/TU-mo) | Verified |
| | Standard | Standard Ingress Events | **\$0.02800000** | 1M Events | Verified |
| **Storage (Blob)** | Cool GRS | Cool GRS Data Stored | **\$0.02200000** | 1 GB/Month | Verified |
| | Cool GRS | Cool GRS Write Operations | **\$0.20000000** | 10K Ops | Verified |
| | Cool GRS | Cool Read Operations | **\$0.01300000** | 10K Ops | Verified |
| **Log Analytics** | Analytics Logs | Analytics Logs Data Ingestion | **\$3.34000000** | 1 GB | Verified |
| | Analytics Logs | Analytics Logs Data Retention | **\$0.15000000** | 1 GB/Month (>31 days) | Verified (<=30 days free) |
| **Key Vault** | Standard | Operations | **\$0.03000000** | 10K Ops | Verified |
| **Bandwidth** | Standard | Standard Data Transfer Out | **\$0.00000000** | 1 GB (1st 100 GB free) | Verified |

---

## 4. Workload Assumptions & Sizing Profiles

### 4.1 Per-Developer Workload Baseline
- **Working Days**: 20 days/month (8 hours/day)
- **AI Tool Interactions**: Average **100 invocations / developer / day**
- **Monthly Invocations**: 100 × 20 = **2,000 events / developer / month**
- **Audit Record Sizing**:
  - `audit-trail.jsonl` (Compact Ledger): **1 KB / event**
  - `forensic-trail.jsonl` (Full Forensic Trail): **15 KB / event**
  - Combined Size: **16 KB / event** (~32 MB / developer / month)

### 4.2 Sizing Profile Parameters

| Profile | Projects | Developers | Monthly Events | Total Ingestion (GB) | Peak TPS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Small (PoC / Team)** | 3 PJ | 15 devs | 30,000 | 0.48 GB | 0.5 req/sec |
| **Medium (Department)** | 20 PJ | 100 devs | 200,000 | 3.20 GB | 3.5 req/sec |
| **Large (Enterprise)** | 100 PJ | 1,000 devs | 2,000,000 | 32.00 GB | 35.0 req/sec |

---

## 5. Detailed Cost Breakdown by Sizing Profile

### 5.1 Profile 1: Small (PoC / Team Deployment)
- **Parameters**: 3 Projects, 15 Developers, 30,000 requests/mo, 0.48 GB/mo
- **Allocations**: 1 Container App replica (0.5 vCPU / 1.0 GiB), 1 Event Hubs TU

| Component | Sizing Details | Monthly Cost (USD) | Monthly Cost (JPY) | Share (%) |
| :--- | :--- | :--- | :--- | :--- |
| **Azure Container Apps** | 1 replica (0.5 vCPU / 1.0 GiB) | \$10.89 | ¥1,633 | 31.4% |
| **Azure Event Hubs** | 1 TU (\$21.60) + 30k events | \$21.60 | ¥3,240 | 62.2% |
| **Azure Blob Storage** | 0.48 GB storage + 30k writes | \$0.61 | ¥92 | 1.8% |
| **Azure Log Analytics** | 0.48 GB ingestion (30d hot retention) | \$1.60 | ¥240 | 4.6% |
| **Key Vault / Egress** | Operations & Bandwidth (<100GB) | \$0.03 | ¥4 | 0.1% |
| **Total Monthly** | — | **\$34.73** | **¥5,210** | **100.0%** |
| **Total Annual** | — | **\$416.77** | **¥62,516** | — |
| **Per Developer / Mo** | Divided by 15 | **\$2.32 / dev** | **~¥347 / dev-mo** | — |

---

### 5.2 Profile 2: Medium (Department / BU Deployment)
- **Parameters**: 20 Projects, 100 Developers, 200,000 requests/mo, 3.20 GB/mo
- **Allocations**: 2 Container App replicas (HA redundant), 1 Event Hubs TU

| Component | Sizing Details | Monthly Cost (USD) | Monthly Cost (JPY) | Share (%) |
| :--- | :--- | :--- | :--- | :--- |
| **Azure Container Apps** | 2 replicas redundant | \$21.77 | ¥3,266 | 37.4% |
| **Azure Event Hubs** | 1 TU (\$21.60) + 200k events | \$21.61 | ¥3,241 | 37.1% |
| **Azure Blob Storage** | 3.2 GB storage + 200k writes | \$4.07 | ¥611 | 7.0% |
| **Azure Log Analytics** | 3.2 GB ingestion (30d hot retention) | \$10.69 | ¥1,603 | 18.4% |
| **Key Vault / Egress** | Operations & Bandwidth (<100GB) | \$0.03 | ¥4 | 0.1% |
| **Total Monthly** | — | **\$58.17** | **¥8,725** | **100.0%** |
| **Total Annual** | — | **\$698.00** | **¥104,700** | — |
| **Per Developer / Mo** | Divided by 100 | **\$0.58 / dev** | **~¥87 / dev-mo** | — |

---

### 5.3 Profile 3: Large (Enterprise-Wide Governance)
- **Parameters**: 100 Projects, 1,000 Developers, 2,000,000 requests/mo, 32.00 GB/mo
- **Allocations**: 3 Container App replicas avg (autoscale up to 10), 2 Event Hubs TUs

| Component | Sizing Details | Monthly Cost (USD) | Monthly Cost (JPY) | Share (%) |
| :--- | :--- | :--- | :--- | :--- |
| **Azure Container Apps** | 3 replicas avg (up to 10 autoscale) | \$35.04 | ¥5,255 | 15.5% |
| **Azure Event Hubs** | 2 TUs (\$43.20) + 2M events | \$43.26 | ¥6,488 | 19.1% |
| **Azure Blob Storage** | 32 GB storage + 2M writes | \$40.70 | ¥6,106 | 18.0% |
| **Azure Log Analytics** | 32 GB ingestion (30d hot retention) | \$106.88 | ¥16,032 | 47.3% |
| **Key Vault / Egress** | Operations & Bandwidth (<100GB) | \$0.03 | ¥4 | 0.1% |
| **Total Monthly** | — | **\$225.91** | **¥33,886** | **100.0%** |
| **Total Annual** | — | **\$2,710.86** | **¥406,629** | — |
| **Per Developer / Mo** | Divided by 1,000 | **\$0.23 / dev** | **~¥34 / dev-mo** | — |

---

## 6. Long-Term Storage Accumulation (3-Year WORM Immutability)

Per [`infra/azure/variables.tf`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/infra/azure/variables.tf), audit logs are locked under an immutable WORM policy for **3 years (1,095 days)**.

| Elapsed Timeline | Small Cumulative / Mo | Medium Cumulative / Mo | Large Cumulative / Mo |
| :--- | :--- | :--- | :--- |
| **Month 1 (Initial)** | 0.48 GB / \$0.61 (¥92) | 3.2 GB / \$4.07 (¥611) | 32 GB / \$40.70 (¥6,106) |
| **Month 12 (Year 1)** | 5.76 GB / \$0.73 (¥109) | 38.4 GB / \$4.84 (¥727) | 384 GB / \$48.45 (¥7,267) |
| **Month 24 (Year 2)** | 11.52 GB / \$0.85 (¥128) | 76.8 GB / \$5.69 (¥853) | 768 GB / \$56.90 (¥8,534) |
| **Month 36 (Year 3 plateau)**| 17.28 GB / \$0.98 (¥147) | 115.2 GB / \$6.53 (¥980) | 1,152 GB / \$65.34 (¥9,802) |

---

## 7. FinOps Optimization Strategies

1. **Dual-Stream Routing Separation (Up to 45% Total Savings)**:
   Route only `audit-trail.jsonl` (1 KB) into Log Analytics for real-time monitoring and KQL queries, while streaming `forensic-trail.jsonl` (15 KB) directly to Blob Storage WORM via Event Hubs Capture. Reduces Log Analytics ingestion from 32 GB to 2 GB, lowering monthly enterprise cost from \$225.91 to **\$125.71 (~¥18,856 / mo; ~¥19 / dev-mo)**.
2. **Off-Hours Container Scaling**: Schedule minimal replicas (scale to 1 or 0) outside core developer hours (20:00–08:00 and weekends).
3. **Event Hubs Auto-Inflate**: Provision 1 baseline TU with auto-inflate enabled rather than over-provisioning static TUs.
4. **Hybrid Local/Cloud MCP Model**: Enforce zero-cost Local MCP for non-sensitive repositories, reserving Cloud MCP for regulated and sensitive codebases.

---

## 8. Verification Reproducibility & Scripts

To deterministically re-verify all retail rates against the Azure Retail Prices API, execute:

```powershell
$services = @("Container Apps", "Event Hubs", "Storage", "Log Analytics", "Key Vault")
foreach ($svc in $services) {
    $uri = "https://prices.azure.com/api/retail/prices?`$filter=contains(serviceName, '$svc') and armRegionName eq 'japaneast'"
    $res = Invoke-RestMethod -Uri $uri
    Write-Host "=== $svc ==="
    $res.Items | Select-Object -First 3 -Property serviceName, skuName, meterName, unitPrice, unitOfMeasure
}
```
