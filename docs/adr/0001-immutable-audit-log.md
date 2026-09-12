---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "adr"
id: "ADR-0001"
title: "ADR-0001: Cryptographic Hash Chain for Audit Log Immutability"
version: "1.0.0"
status: "active"
language: "en"
canonical_ref: "docs/adr/0001-immutable-audit-log.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.1.0"
tags: ["adr", "hash-chain", "immutability", "merkle-tree"]
---

# ADR-0001: Cryptographic Hash Chain for Audit Log Immutability

## Status
Accepted

## Context
AI-assisted software development operations must adhere to legal and corporate compliance standards (e.g. EU AI Act, SOC 2 Type II). If audit logs can be arbitrarily edited or deleted by local developers, audit trails lose evidentiary value.

## Decision
Adopt a blockchain-inspired Merkle Hash Chain structure ($H_i = \text{SHA256}(H_{i-1} + \text{Payload}_i)$) across both `audit-trail.jsonl` and `forensic-trail.jsonl`. Each record embeds the previous block's hash and is cryptographically verified upon audit inspection (`aah verify`).

## Consequences
- Positive: Mathematical proof of tampering, deletion, or reordering.
- Positive: Zero dependency on external distributed ledgers or third-party servers.
- Negative: Modifying historical records requires intentional cryptographic recalculation, which is detected and rejected by `aah verify`.
