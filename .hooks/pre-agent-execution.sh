#!/usr/bin/env bash
# Agent Aegis Harness - Pre-Agent Execution Hook
# Instruments AI agent invocation, validates Policy Digest, and redacts secrets

set -euo pipefail

echo "[AEGIS] Running Sentinel Pre-Execution Gate..."

# Verify policy digest and staged files
if command -v aah >/dev/null 2>&1; then
    aah check --strict
else
    python -m aegis.cli check --strict
fi

echo "[AEGIS] Pre-Execution Gate: PASSED"
