"""
Tests for Cloud Workflow & Remote Agent Audit Module
"""
import base64
import json
import os
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aegis.cli import app
from aegis.cloud_audit.detector import CloudContextDetector
from aegis.cloud_audit.gate import CloudSentinelGate
from aegis.cloud_audit.oidc import OIDCAttestationAdapter
from aegis.cloud_audit.scanner import CloudDiffScanner
from aegis.models import (
    ActorType,
    CloudPlatformType,
    VerdictStatus,
    ViolationSeverity,
)

runner = CliRunner()

def test_cloud_detector_non_ci():
    detector = CloudContextDetector(env={})
    assert not detector.is_ci_environment()
    assert detector.detect() is None

def test_cloud_detector_github_actions():
    mock_env = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_WORKFLOW": "ci-audit.yml",
        "GITHUB_RUN_ID": "987654321",
        "GITHUB_RUN_ATTEMPT": "2",
        "GITHUB_JOB": "sentinel-check",
        "RUNNER_ENVIRONMENT": "github-hosted",
        "GITHUB_EVENT_NAME": "pull_request",
        "GITHUB_ACTOR": "copilot-coding-agent",
        "GITHUB_REF": "refs/pull/105/merge",
        "GITHUB_SHA": "d4e5f6a1b2c3",
        "GITHUB_BASE_REF": "main",
        "ACTIONS_ID_TOKEN_REQUEST_URL": "https://actions.internal/token",
    }
    detector = CloudContextDetector(env=mock_env)
    assert detector.is_ci_environment()
    ctx = detector.detect()
    assert ctx is not None
    assert ctx.platform == CloudPlatformType.GITHUB_ACTIONS
    assert ctx.workflow_name == "ci-audit.yml"
    assert ctx.workflow_run_id == "987654321"
    assert ctx.workflow_run_attempt == 2
    assert ctx.job_id == "sentinel-check"
    assert ctx.actor == "copilot-coding-agent"
    assert ctx.actor_type == ActorType.AUTONOMOUS_CLOUD_AGENT
    assert ctx.pr_number == 105
    assert ctx.head_sha == "d4e5f6a1b2c3"
    assert ctx.base_sha == "main"
    assert ctx.oidc_token_issuer == "https://token.actions.githubusercontent.com"

def test_cloud_detector_actor_classification():
    detector = CloudContextDetector(env={})
    assert detector._classify_actor("copilot[bot]") == ActorType.AUTONOMOUS_CLOUD_AGENT
    assert detector._classify_actor("github-copilot-agent") == ActorType.AUTONOMOUS_CLOUD_AGENT
    assert detector._classify_actor("dependabot[bot]") == ActorType.BOT
    assert detector._classify_actor("github-actions") == ActorType.BOT
    assert detector._classify_actor("release-bot") == ActorType.BOT
    assert detector._classify_actor("sun-flat-yamada") == ActorType.HUMAN

def test_oidc_adapter_parse_jwt():
    adapter = OIDCAttestationAdapter(env={})
    
    # ダミー JWT 生成
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": "https://token.actions.githubusercontent.com",
        "sub": "repo:sun-flat-yamada/agent-aegis-harness:ref:refs/pull/105/merge",
        "aud": "aegis-audit",
        "repository": "sun-flat-yamada/agent-aegis-harness",
        "repository_owner": "sun-flat-yamada",
        "ref": "refs/pull/105/merge",
        "sha": "d4e5f6a1b2c3",
        "workflow": ".github/workflows/ci.yml",
        "run_id": "987654321",
    }
    
    b64_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    b64_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    raw_jwt = f"{b64_header}.{b64_payload}.dummysignature"
    
    claim = adapter.parse_jwt_claim(raw_jwt)
    assert claim is not None
    assert claim.iss == "https://token.actions.githubusercontent.com"
    assert claim.aud == "aegis-audit"
    assert claim.repository == "sun-flat-yamada/agent-aegis-harness"
    assert claim.run_id == "987654321"
    assert len(claim.raw_token_sha256) == 64

def test_diff_scanner_clean():
    scanner = CloudDiffScanner()
    clean_diff = """
diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1,3 +1,4 @@
+def greet():
+    return "hello"
"""
    result = scanner.scan_text(clean_diff, modified_files=["src/app.py"])
    assert result.is_clean
    assert len(result.violations) == 0
    assert len(result.masked_findings) == 0

def test_diff_scanner_secret_leak():
    scanner = CloudDiffScanner()
    leaked_diff = """
diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -1,2 +1,3 @@
+AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'
"""
    result = scanner.scan_text(leaked_diff, modified_files=["config.py"])
    assert not result.is_clean
    assert any(v.rule_id == "RULE-CLOUD-SECRET-LEAK" for v in result.violations)
    assert any(v.severity == ViolationSeverity.CRITICAL for v in result.violations)

def test_diff_scanner_protected_files():
    scanner = CloudDiffScanner()
    mod_diff = """
diff --git a/.aegis/rules/security.yaml b/.aegis/rules/security.yaml
--- a/.aegis/rules/security.yaml
+++ b/.aegis/rules/security.yaml
@@ -1 +1,2 @@
+new_rule: disable
"""
    result = scanner.scan_text(mod_diff, modified_files=[".aegis/rules/security.yaml"])
    assert not result.is_clean
    assert any(v.rule_id == "RULE-CLOUD-PROTECTED-FILE" for v in result.violations)
    assert any(v.severity == ViolationSeverity.MEDIUM for v in result.violations)

def test_cloud_sentinel_gate_export_github_output():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tf:
        out_file = tf.name

    try:
        mock_env = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_WORKFLOW": "ci.yml",
            "GITHUB_RUN_ID": "111",
            "GITHUB_JOB": "audit",
            "GITHUB_ACTOR": "tester",
            "GITHUB_SHA": "abcdef123456",
            "GITHUB_OUTPUT": out_file,
        }
        gate = CloudSentinelGate(env=mock_env)
        gate.export_github_step_outputs(
            verdict_status=VerdictStatus.PASS,
            policy_digest="sha256:dummy",
            violations_count=0,
            files_inspected=3,
        )

        content = Path(out_file).read_text(encoding="utf-8")
        assert "verdict=PASS" in content
        assert "policy_digest=sha256:dummy" in content
        assert "violations_count=0" in content
        assert "files_inspected=3" in content
    finally:
        if os.path.exists(out_file):
            os.remove(out_file)

def test_cli_check_ci():
    result = runner.invoke(app, ["check", "--ci"])
    # 実行され、Aegis Cloud Sentinel Gate のレポートが表示されること
    assert "Aegis Cloud Sentinel Gate" in result.stdout
    assert "Policy Digest" in result.stdout
