---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "DOC-SETUP-TARGET-001"
title: "Target Project Setup & Tool Instrumentation Guide"
version: "1.2.0"
status: "active"
language: "en"
canonical_ref: "docs/setup/target-project-guide.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "windsurf", "cli"]
  min_aah_version: "0.1.0"
tags: ["setup", "target-project", "hooks", "antigravity", "claude-code", "github-copilot", "copilot-app", "copilot-cli"]
---

# Target Project Setup & Tool Instrumentation Guide

This guide explains how to install, instrument, and configure Agent Aegis Harness (`aah`) within existing software repositories to monitor and govern AI agents without introducing developer friction.

---

## 1. Quick Installation & Automation Breakdown

### 1.1 Command Execution

Install the harness in your project environment and run initialization:

```bash
# Add as developer dependency
pip install agent-aegis-harness

# Initialize Aegis governance bundle in repository root
aah init
```

### 1.2 Out-of-the-Box Automation & User Customization Requirements

A critical question is: *"Does running `aah init` complete everything automatically, or do I need to manually configure files?"*

The answer is: **For standard daily development, `aah init` fully automates setup out-of-the-box.**

- **What `aah init` DOES automatically:**
  1. **Governance Asset Provisioning**: Creates `.aegis/rules/` (active policies), `.aegis/schemas/` (JSON schemas), `.aegis/templates/`, `.aegis/logs/`, `.aegis/instructions/`, `.hooks/`, and `.skills/`.
  2. **Configuration Initialization**: Generates `.aegis/config.yaml` with recommended guardrail levels.
  3. **Instruction Rule Generation**: Prepares standard rule definitions (`.aegis/instructions/aegis-copilot-rules.md`, `aegis-claude-rules.md`, `aegis-system-governance.md`).
  4. **Non-Destructive Pointer Injection**: Detects existing AI tool instruction files and safely appends (or creates) a 1-line reference pointer without overwriting or destroying your existing project prompts:
     - `.github/copilot-instructions.md` (for GitHub Copilot)
     - `CLAUDE.md` (for Claude Code)
     - `.cursorrules` (for Cursor)
     - `.amazonq/rules.md` (for Amazon Q / AWS Kiro)
  5. **Hook Script Generation**: Generates `.hooks/pre-agent-execution.sh` and `.hooks/post-agent-execution.sh`.
  6. **Cryptographic Policy Hashing**: Computes the initial deterministic SHA-256 digest of rules and schemas.

Because supported AI tools (GitHub Copilot in IDEs, Claude Code, Cursor) natively read these instruction files directly from the repository workspace, **no external configuration files, IDE settings, or shell profiles need to be manually edited for standard operation.**

- **Mandatory Requirements When User Customization Exists:**
  If your project already maintains or customizes its own instruction files or policies, you must adhere to the following mandatory rules:
  1. **Preserving Injection Pointers**: If you customize `.github/copilot-instructions.md`, `CLAUDE.md`, `.cursorrules`, or `.amazonq/rules.md`, you **MUST ensure that the Aegis injection pointer block (`<!-- AEGIS-AUDIT-INJECTION -->`) is preserved**. If this marker is removed, the AI agent will lose connection to Aegis governance rules.
  2. **Custom Policy Schema Conformance**: If you add project-specific policies under `.aegis/rules/`, they must include valid YAML frontmatter conforming to `.aegis/schemas/frontmatter.schema.json`.
  3. **Mandatory Verification via `aah check`**: Whenever instruction files or policies are edited, run `aah check`. The built-in **Instruction Pointer Integrity** check automatically validates that all required Aegis pointers are present and intact across active AI configuration files, warning or blocking if a pointer was accidentally deleted.

### 1.3 Automation Matrix by AI Tool

| AI Tool / Interface | Out-of-the-Box via `aah init` | Mandatory Action When Customizing | Verification Command |
| :--- | :--- | :--- | :--- |
| **GitHub Copilot (IDE)** | Fully automated (pointer injected) | Retain `<!-- AEGIS-AUDIT-INJECTION -->` in `.github/copilot-instructions.md` | `aah check` / `aah status` |
| **GitHub Copilot App (Web/PR)** | Fully automated (pointer injected) | See Cloud Flow Architecture Blueprint for CI gating | `aah check --strict` |
| **GitHub Copilot CLI** | Wrapper execution | Wrap execution: `aah wrap -- gh copilot ...` | `aah status` |
| **Claude Code** | Fully automated (pointer injected) | Retain `<!-- AEGIS-AUDIT-INJECTION -->` in `CLAUDE.md` | `aah check` / `aah status` |
| **Cursor & Windsurf** | Fully automated (pointer injected) | Retain `<!-- AEGIS-AUDIT-INJECTION -->` in `.cursorrules` | `aah check` / `aah status` |
| **Google Antigravity** | Skills & rules provisioned | Wire `AntigravityAegisAdapter` in SDK agent config | `aah check` |
| **Generic CLI / Scripts** | Wrapper execution | Prefix agent invocation: `aah wrap -- <command>` | `aah verify` |

---

## 2. Tool-by-Tool Guidance

### A. GitHub Copilot (IDE: VS Code, JetBrains, Visual Studio)

GitHub Copilot in IDEs (Chat, Inline Suggestions, Edit mode) operates locally within developer workspaces.

#### 1. Setup & Out-of-the-Box Operation:
`aah init` automatically places the following pointer into `.github/copilot-instructions.md`:
```markdown
<!-- AEGIS-AUDIT-INJECTION -->
Please strictly follow Aegis Governance Rules in `.aegis/instructions/aegis-copilot-rules.md`.
```
VS Code and JetBrains Copilot extensions automatically load this file as workspace custom instructions. No manual settings adjustments are required.

#### 2. Mandatory Rule on Customization:
If your project defines its own team prompt or coding style in `.github/copilot-instructions.md`, keep the Aegis injection pointer block intact at the top or bottom of the file. Run `aah check` to verify pointer integrity.

*(Optional Advanced Note: For organizations running the Aegis MCP Security Gateway to inspect Copilot Chat tool invocations in real time, configure `"github.copilot.advanced": {"mcpServers": {"aegis": {"type": "stdio", "command": "aah", "args": ["mcp-server", "--mode", "local"]}}}` in `.vscode/settings.json`).*

---

### B. GitHub Copilot App (GitHub.com Web, PR Reviews, Copilot Workspace, Coding Agent)

Cloud-hosted GitHub Copilot features (such as automated PR reviews and Copilot Workspace) execute on GitHub's remote infrastructure.

#### 1. Setup & Out-of-the-Box Operation:
- Cloud Copilot reads repository custom instructions from `.github/copilot-instructions.md`, which is initialized by `aah init`.

#### 2. Cloud Workflow Governance Architecture:
Because cloud-based agents run in remote ephemeral environments where local developer hooks cannot execute, a dedicated cloud runner and CI workflow audit architecture is required.  
The complete technical specification and design for cloud workflow auditing is detailed in [`.devs/changes/2026-09-12_AddSupportCloudFlowAudit/blueprint.md`](../../.devs/changes/2026-09-12_AddSupportCloudFlowAudit/blueprint.md).

---

### C. GitHub Copilot CLI (`gh copilot`)

GitHub Copilot CLI provides command suggestions and explanations directly in terminal shells (`gh copilot suggest`, `gh copilot explain`).

#### 1. Execution Protection via `aah wrap`:
Prefix CLI commands with `aah wrap --`. Sentinel intercepts planned commands before execution, blocks destructive commands (`rm -rf /`, secret exfiltration), and records 5W1H audit records:
```bash
# Protected suggestion
aah wrap -- gh copilot suggest -t shell "find and clean empty temp directories"

# Protected explanation
aah wrap -- gh copilot explain "kill -9 1234"
```

#### 2. Convenient Shell Aliases (Optional):
You may optionally add an alias in your shell configuration:
- **Bash / Zsh (`~/.bashrc`, `~/.zshrc`):**
  ```bash
  alias gh-copilot='aah wrap -- gh copilot'
  alias ghcs='aah wrap -- gh copilot suggest -t shell'
  alias ghce='aah wrap -- gh copilot explain'
  ```
- **PowerShell (`$PROFILE`):**
  ```powershell
  function gh-copilot { aah wrap -- gh copilot @args }
  function ghcs { aah wrap -- gh copilot suggest -t shell @args }
  function ghce { aah wrap -- gh copilot explain @args }
  ```

---

### D. Google Antigravity (SDK / IDE)

#### 1. Out-of-the-Box Operation:
`aah init` provisions governance skills and rule definitions under `.skills/` and `.aegis/rules/`.

#### 2. Python SDK Integration:
In custom agent scripts, register the Aegis adapter on `LocalAgentConfig`:
```python
from aegis.recorder.antigravity_adapter import AntigravityAegisAdapter
from google.antigravity.sdk import LocalAgentConfig

def configure_agent():
    config = LocalAgentConfig()
    adapter = AntigravityAegisAdapter(repo_path=".")
    config.hooks = adapter.register_hooks(config.hooks)
    return config
```

---

### E. Claude Code

#### 1. Setup & Out-of-the-Box Operation:
`aah init` automatically appends or creates `CLAUDE.md` with:
```markdown
<!-- AEGIS-AUDIT-INJECTION -->
@.aegis/instructions/aegis-claude-rules.md
```
Claude Code automatically reads `CLAUDE.md` when launched in the workspace.

#### 2. Mandatory Rule on Customization:
If customizing `CLAUDE.md`, retain the `@.aegis/instructions/aegis-claude-rules.md` pointer line. `aah check` verifies that this pointer remains intact.

---

### F. Cursor & Windsurf

#### 1. Setup & Out-of-the-Box Operation:
`aah init` automatically appends or creates `.cursorrules` with:
```markdown
# <!-- AEGIS-AUDIT-INJECTION -->
# Follow .aegis/instructions/aegis-system-governance.md
```

#### 2. Mandatory Rule on Customization:
If adding custom project rules to `.cursorrules`, retain the Aegis governance comment block.

---

### G. Generic CLI / Scripts

For custom scripts or automation executing AI commands, wrap invocations with `aah wrap`:
```bash
aah wrap -- claude "fix vulnerability in src/auth.py"
aah wrap -- python my_agent_script.py --run
```

---

## 3. Verification & Diagnostics

After running `aah init` or making customizations, verify your project's governance health:

### 3.1 Check Instrumentation Status (`aah status`)
Run `aah status` to verify all instruction pointers, the MCP Security Gateway, and the audit WAL:
```bash
aah status
```
Expected output:
```text
                     Aegis Multi-AI Instrumentation Status                      
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Component           ┃ Target / Mode                    ┃ Status              ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ Claude Code Pointer │ CLAUDE.md                        │ ACTIVE              │
│ VSCode Copilot Pntr │ .github/copilot-instructions.md  │ ACTIVE              │
│ AWS Kiro / Q Pointer│ .amazonq/rules.md                │ ACTIVE              │
│ Cursor Pointer      │ .cursorrules                     │ ACTIVE              │
│ MCP Gateway         │ Local (Default: STDIO)           │ READY               │
│ Local SQLite WAL    │ aegis_wal.db                     │ ONLINE              │
└─────────────────────┴──────────────────────────────────┴─────────────────────┘
```

### 3.2 Instant Sentinel Audit (`aah check`)
Run `aah check` to verify policy hashes, secret masking, and **Instruction Pointer Integrity**:
```bash
aah check
```
Expected output:
```text
[AUDIT] Running Sentinel Instant Audit...
                             Sentinel Audit Verdict                             
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Category                      ┃ Status ┃ Details                             ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ PII / Secret Redactor         │ PASSED │ Pattern rules active (0 leaks in    │
│                               │        │ git staged)                         │
│ Context Drift Integrity       │ PASSED │ Compaction drift score: 0.04        │
│                               │        │ (Threshold: 0.20)                   │
│ Instruction Pointer Integrity │ PASSED │ All 4 active instruction pointers   │
│                               │        │ verified                            │
│ Policy Digest Match           │ PASSED │ sha256:ed961461c97... (5 policies)  │
│ Skill Tool Whitelist          │ PASSED │ 10 tools approved in                │
│                               │        │ .aegis/rules/skill-compliance-poli… │
│ Cryptographic Log Chain       │ PASSED │ 3 blocks cryptographically verified │
└───────────────────────────────┴────────┴─────────────────────────────────────┘
[OK] All Sentinel Instant Audit gates passed.
```

If an instruction pointer was accidentally deleted during custom editing, `Instruction Pointer Integrity` will flag `WARN`:
`Missing Aegis pointer in: .github/copilot-instructions.md (Run 'aah init')`
