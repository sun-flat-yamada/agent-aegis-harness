---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "adr"
id: "ADR-0002"
title: "ADR-0002: Decoupling Real-time Auditing from Offline Self-Refinement"
version: "1.0.0"
status: "active"
language: "en"
canonical_ref: "docs/adr/0002-decoupled-refinement.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.1.0"
tags: ["adr", "refinement", "decoupling", "reproducibility"]
---

# ADR-0002: Decoupling Real-time Auditing from Offline Self-Refinement

## Status
Accepted

## Context
When AI systems automatically adapt rules based on generated outputs, combining auditing and rule updates in the same real-time loop creates non-deterministic drift. An auditor cannot reliably determine which policy version governed a specific historical execution.

## Decision
Separate real-time auditing (Sentinel & Archivist) from continuous optimization (Refiner). Sentinel evaluates actions against a fixed `policy_hash_digest`, while Refiner operates purely as an offline batch activity that proposes rule updates via Human-in-the-Loop Pull Requests.

## Consequences
- Positive: Deterministic historical audit reproducibility.
- Positive: Governance changes remain transparent and reviewable in Git history.
- Negative: Rule improvements require human PR review rather than instantaneous autonomous live updates.
