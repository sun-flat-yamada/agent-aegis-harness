---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "DOC-SETUP-TARGET-001"
title: "Target Project Setup & Tool Instrumentation Guide"
version: "1.0.0"
status: "active"
language: "en"
canonical_ref: "docs/setup/target-project-guide.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.1.0"
tags: ["setup", "target-project", "hooks", "antigravity", "claude-code"]
---

# Target Project Setup & Tool Instrumentation Guide

This guide explains how to install and configure Agent Aegis Harness (`aah`) within existing software repositories to monitor and govern AI agents without introducing developer friction.

## 1. Quick Installation

```bash
# Add as developer dependency
pip install agent-aegis-harness

# Initialize Aegis governance bundle in repository root
aah init
```

The `aah init` command automatically provisions:
```text
.aegis/
├── config.yaml          # Project-specific governance settings
├── rules/               # Active policies (security, drift, compliance)
├── schemas/             # JSON Schemas (audit-event, frontmatter)
├── templates/           # Report templates
└── logs/                # Audit trails
.hooks/                  # Agent lifecycle hooks
.skills/                 # AI assistant skills
```

---

## 2. Tool-by-Tool Instrumentation

### A. Google Antigravity (SDK / IDE)
Aegis provides a built-in adapter for Antigravity lifecycle hooks:
```python
from aegis.recorder.antigravity_adapter import AntigravityAegisAdapter
from google.antigravity.sdk import LocalAgentConfig

def configure_agent():
    config = LocalAgentConfig()
    adapter = AntigravityAegisAdapter(repo_path=".")
    config.hooks = adapter.register_hooks(config.hooks)
    return config
```
This automatically captures:
- `pre_turn`: Prompt sanitization & injection check
- `pre_tool_call_decide`: Instant Sentinel Tier 1 blocking of dangerous commands
- `post_tool_call`: Diff stat and file modification auditing
- `on_compaction`: Context drift scoring

### B. Claude Code
Register `.hooks/pre-agent-execution.sh` and `.hooks/post-agent-execution.sh` in your Claude settings (`~/.claude/settings.json` or repo settings):
```json
{
  "hooks": {
    "pre_tool_call": "./.hooks/pre-agent-execution.sh",
    "post_tool_call": "./.hooks/post-agent-execution.sh"
  }
}
```

### C. Cursor & Windsurf
Add Aegis governance compliance instructions into `.cursorrules`:
```markdown
Before executing shell modifications or critical file overwrites, always verify actions via:
  aah wrap -- <command>
```

### D. Generic CLI / Scripts
Wrap any agent invocation using `aah wrap`:
```bash
aah wrap -- claude "fix vulnerability in src/auth.py"
```

---

## 3. Verification & Health Check

Run `aah check` to verify that all policies, schemas, and redactor patterns are active:
```bash
aah check
```
If all categories show `PASSED`, your project is guarded by Aegis Sentinel.
