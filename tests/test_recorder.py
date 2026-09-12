"""
Tests for Aegis Recorder (Dual-Stream Logging and Schema Compliance)
"""
import json
import pytest
from datetime import datetime
from aegis.models import (
    AegisAuditEvent,
    AuditReproducibility,
    EnvironmentInfo,
    ClientToolType,
    TriggerContext,
    RetrievalContext,
    InferenceTrace,
    ActionPayload,
    SentinelVerdict,
    VerdictStatus,
    IntegrityProof,
)
from aegis.recorder.tracer import AegisRecorder
from aegis.archivist.integrity import HashChainManager

def test_recorder_dual_stream_writes_and_verifies(tmp_path):
    """Recorder が audit-trail と forensic-trail に正しく書き込み、Hash Chain が成立することを検証"""
    audit_log = tmp_path / "audit-trail.jsonl"
    forensic_log = tmp_path / "forensic-trail.jsonl"
    
    recorder = AegisRecorder(
        audit_trail_path=audit_log,
        forensic_trail_path=forensic_log,
    )
    
    event = AegisAuditEvent(
        trace_id="12345678-1234-5678-1234-567812345678",
        span_id="span-001",
        step_index=1,
        timestamp=datetime.utcnow(),
        audit_reproducibility=AuditReproducibility(
            policy_bundle_version="v1.0.0",
            policy_hash_digest="sha256:dummy",
            sentinel_version="0.1.0",
            evaluator_engine="ast-rule",
        ),
        environment=EnvironmentInfo(
            client_tool=ClientToolType.ANTIGRAVITY,
            repository="test-repo",
            git_commit="abc1234",
        ),
        trigger=TriggerContext(
            source="user_prompt",
            sanitized_prompt="Hello Aegis",
        ),
        sentinel_verdict=SentinelVerdict(
            status=VerdictStatus.PASS,
            score=100.0,
            tier_level="TIER_1_AST",
            violations=[],
        ),
        integrity=IntegrityProof(
            previous_record_hash=HashChainManager.GENESIS_HASH,
            current_record_hash="pending",
        ),
    )
    
    recorded_event = recorder.record(event)
    
    assert audit_log.exists()
    assert forensic_log.exists()
    
    # audit-trail の整合性を検証
    success, count, err = HashChainManager.verify_log_file(audit_log)
    assert success is True
    assert count == 1
    assert err is None

    # forensic-trail の整合性も検証
    f_success, f_count, f_err = HashChainManager.verify_log_file(forensic_log)
    assert f_success is True
    assert f_count == 1
    assert f_err is None

def test_recorder_independent_hash_chains_across_sessions(tmp_path):
    """複数プロセス/インスタンスにまたがる記録でも両ストリームの Hash Chain が断裂しないことを検証"""
    audit_log = tmp_path / "audit-trail.jsonl"
    forensic_log = tmp_path / "forensic-trail.jsonl"

    for i in range(1, 4):
        # 毎回新しい Recorder インスタンスを生成（新セッション/プロセスのシミュレーション）
        rec = AegisRecorder(audit_trail_path=audit_log, forensic_trail_path=forensic_log)
        event = AegisAuditEvent(
            trace_id=f"trace-{i}",
            span_id=f"span-{i}",
            step_index=i,
            timestamp=datetime.utcnow(),
            audit_reproducibility=AuditReproducibility(
                policy_bundle_version="v1.0.0",
                policy_hash_digest="sha256:test",
                sentinel_version="0.1.0",
                evaluator_engine="ast-rule",
            ),
            environment=EnvironmentInfo(
                client_tool=ClientToolType.CLI,
                repository="test-repo",
                git_commit="HEAD",
            ),
            trigger=TriggerContext(source="user_prompt", sanitized_prompt=f"cmd {i}"),
            sentinel_verdict=SentinelVerdict(status=VerdictStatus.PASS, score=100.0, tier_level="TIER_1_AST", violations=[]),
            integrity=IntegrityProof(previous_record_hash="pending", current_record_hash="pending"),
        )
        rec.record(event)

    # 両方のログが 3 ブロック完全検証されることを確認
    a_ok, a_count, a_err = HashChainManager.verify_log_file(audit_log)
    assert a_ok is True
    assert a_count == 3
    assert a_err is None

    f_ok, f_count, f_err = HashChainManager.verify_log_file(forensic_log)
    assert f_ok is True
    assert f_count == 3
    assert f_err is None
