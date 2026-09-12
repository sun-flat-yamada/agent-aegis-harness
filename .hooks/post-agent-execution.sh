#!/usr/bin/env bash
# Agent Aegis Harness - Post-Agent Execution Hook
# Verifies Hash Chain cryptographic integrity and generates audit report

set -euo pipefail

echo "[AEGIS] Running Sentinel Post-Execution Integrity Sealing..."

if command -v aah >/dev/null 2>&1; then
    aah verify --log-file .aegis/logs/audit-trail.jsonl
    aah verify --log-file .aegis/logs/forensic-trail.jsonl
    aah report -o .aegis/reports/latest-audit-report.md
else
    python -m aegis.cli verify --log-file .aegis/logs/audit-trail.jsonl
    python -m aegis.cli verify --log-file .aegis/logs/forensic-trail.jsonl
    python -m aegis.cli report -o .aegis/reports/latest-audit-report.md
fi

echo "[AEGIS] Post-Execution Sealing: COMPLETED"
