---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "DOC-SETUP-TARGET-001"
title: "Target Project Setup & Tool Instrumentation Guide"
version: "1.1.0"
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

### 1.2 What `aah init` Automates vs. What Requires Manual Setup

A common question is: *"Does running `aah init` complete everything automatically, or do I need to manually configure files?"*

The boundary is clearly defined:

- **What `aah init` DOES automatically:**
  1. **Directory Provisioning**: Creates `.aegis/rules/`, `.aegis/schemas/`, `.aegis/templates/`, `.aegis/logs/`, `.aegis/instructions/`, `.hooks/`, and `.skills/`.
  2. **Configuration Initialization**: Generates default `.aegis/config.yaml` if not already present.
  3. **Instruction Rule Generation**: Prepares standard rule files (`.aegis/instructions/aegis-copilot-rules.md`, `aegis-claude-rules.md`, `aegis-system-governance.md`).
  4. **Non-Destructive Pointer Injection**: Inspects existing AI instruction files and safely appends (or creates) a 1-line pointer without overwriting your existing prompts or guidelines:
     - `.github/copilot-instructions.md` (for GitHub Copilot)
     - `CLAUDE.md` (for Claude Code)
     - `.cursorrules` (for Cursor)
     - `.amazonq/rules.md` (for Amazon Q / AWS Kiro)
  5. **Hook Script Generation**: Generates `.hooks/pre-agent-execution.sh` and `.hooks/post-agent-execution.sh`.
  6. **Cryptographic Policy Hashing**: Computes the initial deterministic SHA-256 digest of rules and schemas.

- **What `aah init` CANNOT do automatically (Manual User Actions Required):**
  - **Git Operations**: `aah init` creates/updates local files, but **does not run git add/commit/push**. You must commit these files to your repository.
  - **External Tool Settings**: Settings stored outside the repository (such as `~/.claude/settings.json` for Claude Code hooks, or shell profiles `~/.bashrc` / `$PROFILE` for CLI aliases) cannot be modified automatically.
  - **IDE Settings**: Tool configurations inside `.vscode/settings.json` (such as MCP gateway bindings for Copilot) require project-specific settings.
  - **Cloud CI/CD Gates**: GitHub Actions workflows for server-side agents (such as GitHub Copilot App) must be placed in `.github/workflows/`.
  - **Python SDK Integrations**: Attaching the Antigravity adapter requires adding hook registration code to your agent configuration.

### 1.3 Automation Matrix by AI Tool

| AI Tool / Interface | Automatic by `aah init` | Manual Action Required? | Key Configuration Path / Command |
| :--- | :--- | :--- | :--- |
| **GitHub Copilot (IDE)** | Instruction pointer injected | **Yes** (Git commit, optional MCP & Git hook) | `.github/copilot-instructions.md`, `.vscode/settings.json` |
| **GitHub Copilot App (Web/PR)** | Instruction pointer injected | **Yes** (Push to default branch, CI workflow) | `.github/workflows/aegis-sentinel.yml` |
| **GitHub Copilot CLI** | None (CLI execution) | **Yes** (Command wrapping / shell aliases) | `aah wrap -- gh copilot ...`, shell profile |
| **Google Antigravity** | Skills & rules directory created | **Yes** (Hook registration in SDK or IDE) | Python agent config / Antigravity IDE |
| **Claude Code** | Pointer injected, `.hooks/` generated | **Yes** (Hook registration in Claude settings) | `~/.claude/settings.json` |
| **Cursor & Windsurf** | Pointer injected into `.cursorrules` | **Optional** (Add command wrap instructions) | `.cursorrules` |
| **Generic CLI / Scripts** | None | **Yes** (Prefix invocations with `aah wrap`) | CLI command lines |

---

## 2. Tool-by-Tool Detailed Instrumentation

### A. GitHub Copilot (IDE: VS Code, JetBrains, Visual Studio)

GitHub Copilot in IDEs (Chat, Inline Suggestions, Edit mode) operates locally within developer workspaces.

#### 1. What `aah init` Did Automatically:
`aah init` generated or safely appended the following pointer line to `.github/copilot-instructions.md`:
```markdown
<!-- AEGIS-AUDIT-INJECTION -->
Please strictly follow Aegis Governance Rules in `.aegis/instructions/aegis-copilot-rules.md`.
```

#### 2. Manual Actions Required by Developer:

- **Step 1: Commit and push instructions to Git**  
  GitHub Copilot reads workspace instructions from the repository. Commit the newly generated files:
  ```bash
  git add .github/copilot-instructions.md .aegis/
  git commit -m "chore(aegis): instrument GitHub Copilot workspace instructions"
  ```

- **Step 2 (Optional but Recommended): Configure VS Code MCP Security Gateway**  
  To route Copilot Chat tool invocations (such as bash command execution or file edits) through the Aegis Sentinel inspection engine, add the MCP gateway to `.vscode/settings.json`:
  ```json
  {
    "github.copilot.advanced": {
      "mcpServers": {
        "aegis": {
          "type": "stdio",
          "command": "aah",
          "args": ["mcp-server", "--mode", "local"]
        }
      }
    }
  }
  ```
  *(For enterprise cloud deployments, replace with `"type": "sse", "url": "https://aegis-mcp.enterprise.internal/v1/mcp"`).*

- **Step 3 (Recommended): Install Git Post-Commit Audit Correlator**  
  To cryptographically bind Copilot-assisted code changes to the local audit trail, add the correlation call to `.git/hooks/post-commit`:
  ```bash
  #!/usr/bin/env bash
  python -c "from aegis.recorder.git_correlator import GitCorrelator; GitCorrelator().run_post_commit()"
  ```
  Ensure execution permissions are granted: `chmod +x .git/hooks/post-commit`.

---

### B. GitHub Copilot App (GitHub.com Web, PR Reviews, Copilot Workspace, Coding Agent)

The GitHub Copilot App and cloud coding agents run entirely on GitHub-managed cloud infrastructure. They do not have access to your local machine or local hook scripts.

#### 1. What `aah init` Did Automatically:
- Prepared `.github/copilot-instructions.md`, which is GitHub's official standard for repository-level custom instructions across GitHub.com.

#### 2. Manual Actions Required by Developer:

- **Step 1: Push Instructions to the Default Branch (`main` / `master`)**  
  > [!IMPORTANT]
  > Cloud-based Copilot agents (PR review assistants, Copilot Workspace, and GitHub Copilot Coding Agent) **only read `.github/copilot-instructions.md` from the repository's default branch**.  
  > Instructions residing only on unmerged feature branches will NOT be loaded by GitHub.com Copilot.

  ```bash
  git checkout main
  git merge <your-setup-branch>
  git push origin main
  ```

- **Step 2: Configure Server-Side CI Governance Gate (Tier 3 Sentinel)**  
  Because cloud-based Copilot agents generate pull requests without running local pre-commit hooks, server-side CI enforcement is required to validate that generated code complies with all policies.
  
  Create `.github/workflows/aegis-sentinel.yml`:
  ```yaml
  name: Aegis Sentinel Governance Gate

  on:
    pull_request:
      branches: [main, master]

  jobs:
    sentinel-audit:
      name: Aegis Sentinel Verification
      runs-on: ubuntu-latest
      steps:
        - name: Check out repository
          uses: actions/checkout@v4

        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: "3.10"

        - name: Install Aegis Harness
          run: pip install agent-aegis-harness

        - name: Run Sentinel Instant Audit
          run: aah check --strict
  ```

- **Step 3: Enable Branch Protection**  
  In your GitHub repository settings under **Settings > Branches > Branch protection rules**, require the `Aegis Sentinel Verification` status check to pass before PRs can be merged.

---

### C. GitHub Copilot CLI (`gh copilot`)

GitHub Copilot CLI provides shell suggestions and command explanations directly in developer terminals (`gh copilot suggest`, `gh copilot explain`).

#### 1. What `aah init` Did Automatically:
- None. CLI commands execute as native terminal processes outside workspace configuration files.

#### 2. Manual Actions Required by Developer:

- **Step 1: Wrap Invocations with `aah wrap`**  
  Prefix any `gh copilot` command with `aah wrap --`. Sentinel intercepts planned commands, blocks high-risk operations (e.g., recursive deletion, secret exfiltration), and logs 5W1H audit records:
  ```bash
  # Suggest commands under Sentinel supervision
  aah wrap -- gh copilot suggest -t shell "find and delete all empty log directories"

  # Explain commands under Sentinel supervision
  aah wrap -- gh copilot explain "find . -type f -exec chmod 644 {} +"
  ```

- **Step 2: Configure Shell Aliases / Wrapper Functions (Recommended)**  
  To avoid typing `aah wrap --` every time, configure an alias or shell function in your profile:

  - **Bash (`~/.bashrc`) or Zsh (`~/.zshrc`):**
    ```bash
    # Aegis Protected GitHub Copilot CLI
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

- **Step 3: Shell Integration with `gh copilot alias`**  
  If you already use GitHub Copilot's shell aliases (such as `eval "$(gh copilot alias -- bash)"`), override the alias in your shell configuration so that the generated aliases pass through `aah wrap`.

---

### D. Google Antigravity (SDK / IDE)

Google Antigravity natively supports two-phase governance and lifecycle hooks.

#### 1. What `aah init` Did Automatically:
- Created `.skills/` and `.aegis/rules/` directories with policy bundle definitions.

#### 2. Manual Actions Required by Developer:

- **For Antigravity Python SDK**: Register the Aegis hook adapter in your agent initialization code:
  ```python
  from aegis.recorder.antigravity_adapter import AntigravityAegisAdapter
  from google.antigravity.sdk import LocalAgentConfig

  def configure_agent():
      config = LocalAgentConfig()
      adapter = AntigravityAegisAdapter(repo_path=".")
      config.hooks = adapter.register_hooks(config.hooks)
      return config
  ```
  This automatically intercepts:
  - `pre_turn`: Prompt sanitization & injection check
  - `pre_tool_call_decide`: Instant Sentinel Tier 1 blocking of dangerous commands
  - `post_tool_call`: File diff recording and modification auditing
  - `on_compaction`: Context drift scoring

- **For Antigravity IDE**: Verify that `.agents/skills` or `.skills/` contains active governance skills (`antigravity-two-phase-governance`, `dev-change-lifecycle`).

---

### E. Claude Code

Claude Code supports file-based guidelines (`CLAUDE.md`) and execution hooks.

#### 1. What `aah init` Did Automatically:
- Appended or created `CLAUDE.md` with:
  ```markdown
  <!-- AEGIS-AUDIT-INJECTION -->
  @.aegis/instructions/aegis-claude-rules.md
  ```
- Generated `.hooks/pre-agent-execution.sh` and `.hooks/post-agent-execution.sh`.

#### 2. Manual Actions Required by Developer:
Register the hooks in your Claude settings (`~/.claude/settings.json` or project-level `.claude/config.json`):
```json
{
  "hooks": {
    "pre_tool_call": "./.hooks/pre-agent-execution.sh",
    "post_tool_call": "./.hooks/post-agent-execution.sh"
  }
}
```

---

### F. Cursor & Windsurf

Cursor and Windsurf support workspace-level system rules.

#### 1. What `aah init` Did Automatically:
- Appended or created `.cursorrules` with:
  ```markdown
  # <!-- AEGIS-AUDIT-INJECTION -->
  # Follow .aegis/instructions/aegis-system-governance.md
  ```

#### 2. Manual Actions Required by Developer:
Ensure `.cursorrules` includes instructions requiring the model to invoke commands through `aah wrap`:
```markdown
Before executing shell modifications or critical file overwrites, always verify actions via:
  aah wrap -- <command>
```

---

### G. Generic CLI / Scripts

For any custom CLI tool or script driving an LLM:

#### 1. What `aah init` Did Automatically:
- None.

#### 2. Manual Actions Required by Developer:
Prefix agent invocations with `aah wrap`:
```bash
aah wrap -- claude "fix vulnerability in src/auth.py"
aah wrap -- python my_agent_script.py --run
```

---

## 3. Verification & Diagnostics

After completing both the automated and manual steps, run the verification commands:

### 3.1 Check Instrumentation Status
Run `aah status` to inspect all instruction pointers, the MCP Security Gateway, and the audit WAL:
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

### 3.2 Instant Sentinel Audit
Run `aah check` to verify policy hashes and detect any unmasked secrets:
```bash
aah check
```
If all checks pass, your project is actively protected by Aegis Sentinel.

### 3.3 Test MCP Security Gateway (If using Copilot or Claude MCP)
Validate that the MCP gateway allows safe tools and blocks forbidden commands:
```bash
aah mcp-server --test
```
