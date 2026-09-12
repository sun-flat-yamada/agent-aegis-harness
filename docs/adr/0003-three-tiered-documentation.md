---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "adr"
id: "ADR-0003"
title: "ADR-0003: Three-Tiered Documentation Structure by Persona"
version: "1.0.0"
status: "active"
language: "en"
canonical_ref: "docs/adr/0003-three-tiered-documentation.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.1.0"
tags: ["adr", "documentation", "personas", "architecture"]
---

# ADR-0003: Three-Tiered Documentation Structure by Persona

## Status
Accepted

## Context
Initial README documentation suffered from bloated guides combining developer setup, auditor operations, and harness evolution instructions into a single page. This created onboarding confusion for target project developers while underspecifying enterprise auditor needs.

## Decision
Structure all documentation into three distinct persona workflows:
1. **Target Project Developers (`docs/setup/target-project-guide.md`)**: Rapid setup, hook instrumentation, zero friction.
2. **Auditors & Compliance Officers (`docs/setup/auditor-setup-guide.md`, `docs/operations/audit-workflows.md`)**: Central infrastructure, WORM storage, verification, forensics.
3. **Harness Engineers (`docs/operations/harness-evolution.md`)**: Policy refinement, schema SemVer, deterministic replay.
The root `README.md` is condensed into a concise quick-reference linking to these dedicated guides.

## Consequences
- Positive: Developers get running in under 2 minutes.
- Positive: Security and audit teams have comprehensive operational specifications.
- Negative: Requires maintaining synchronized English and Japanese document pairs.
