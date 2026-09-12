"""
Tests for Aegis Sentinel (Redactor and Multi-Tiered Judgement)
"""
import pytest
from aegis.models import VerdictStatus
from aegis.sentinel.judge import SentinelJudge
from aegis.sentinel.redactor import SensitiveRedactor

def test_sensitive_redactor_masks_credentials():
    """Redactor が OpenAI キーやシークレットを確実にマスキングすることを検証"""
    redactor = SensitiveRedactor()
    raw_prompt = "Here is my secret sk-abcdef1234567890abcdef1234567890 and email test@example.com."
    
    sanitized, applied = redactor.redact_text(raw_prompt)
    
    assert "sk-" not in sanitized
    assert "[REDACTED_OPENAI_KEY]" in sanitized
    assert "test@example.com" not in sanitized
    assert "[REDACTED_EMAIL]" in sanitized
    assert "openai_api_key" in applied
    assert "email_address" in applied

def test_sensitive_redactor_nested_dict():
    """ネストされた辞書構造（ツール引数）内の機密情報も再帰的にマスキングされることを検証"""
    redactor = SensitiveRedactor()
    data = {
        "headers": {"Authorization": "Bearer my_super_secret_token_12345678"},
        "server_ip": "192.168.1.100",
    }
    
    sanitized, applied = redactor.redact_dict(data)
    
    assert "[REDACTED_IP]" in sanitized["server_ip"]
    assert "generic_credential" in applied or "ipv4_address" in applied

def test_sentinel_blocks_dangerous_commands():
    """危険な破壊コマンド（rm -rf / 等）が Sentinel により BLOCK されることを検証"""
    judge = SentinelJudge(policy_dir=".aegis/rules")
    
    # 危険コマンド
    verdict_bad = judge.evaluate_tool_call(
        tool_name="run_command",
        arguments={"CommandLine": "rm -rf / --no-preserve-root"}
    )
    assert verdict_bad.status == VerdictStatus.BLOCK
    assert verdict_bad.score == 0.0
    assert len(verdict_bad.violations) > 0

    # 安全コマンド
    verdict_good = judge.evaluate_tool_call(
        tool_name="run_command",
        arguments={"CommandLine": "git status"}
    )
    assert verdict_good.status == VerdictStatus.PASS
    assert verdict_good.score == 100.0
    assert len(verdict_good.violations) == 0
