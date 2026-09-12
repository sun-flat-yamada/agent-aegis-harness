"""
Template definitions and target file specs for Non-Destructive Instruction Injection
"""

INJECTION_MARKER = "<!-- AEGIS-AUDIT-INJECTION -->"

# 既存ファイルの末尾に挿入する 1 行ポインタ定義
TARGET_TOOL_DEFINITIONS = {
    "claude": {
        "target_file": "CLAUDE.md",
        "pointer": f"{INJECTION_MARKER}\n@.aegis/instructions/aegis-claude-rules.md\n",
    },
    "copilot": {
        "target_file": ".github/copilot-instructions.md",
        "pointer": f"{INJECTION_MARKER}\nPlease strictly follow Aegis Governance Rules in `.aegis/instructions/aegis-copilot-rules.md`.\n",
    },
    "amazon_q": {
        "target_file": ".amazonq/rules.md",
        "pointer": f"{INJECTION_MARKER}\nRefer and enforce: `.aegis/instructions/aegis-system-governance.md`.\n",
    },
    "cursor": {
        "target_file": ".cursorrules",
        "pointer": f"\n# {INJECTION_MARKER}\n# Follow .aegis/instructions/aegis-system-governance.md\n",
    },
}
