"""
Unit & Integration Tests for Retroactive AI Session Harvester & Correlator
Tests VS Code Copilot Delta JSONL parsing, Git commit & PR multi-tier correlation,
provenance tagging, sensitive redaction, and hash-chain audit trail ingestion.
"""
import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from aegis.archivist.integrity import HashChainManager
from aegis.harvester.copilot_parser import CopilotDeltaSessionParser
from aegis.harvester.discoverer import DiscoveryTarget, LocalStorageDiscoverer
from aegis.harvester.git_correlator import GitCommitMetadata, GitPRCorrelator
from aegis.harvester.retro_auditor import RetroactiveSessionAuditor
from aegis.models import ClientToolType, NormalizedAIEvent, NormalizedTrigger, TriggerSourceType


def test_copilot_delta_stream_replay(tmp_path: Path):
    """VS Code Delta Stream (Kind 0/1/2) の完全リプレイとイベント抽出を検証"""
    session_file = tmp_path / "copilot_sess_01.jsonl"

    # Line 0: Kind 0 (初期スナップショット)
    line0 = json.dumps({
        "kind": 0,
        "v": {
            "version": 3,
            "creationDate": 1775278274000,
            "sessionId": "sess-copilot-test-01",
            "requests": []
        }
    })

    # Line 1: Kind 1 (プロパティ設定: タイトル)
    line1 = json.dumps({
        "kind": 1,
        "k": ["customTitle"],
        "v": "Refactor auth logic"
    })

    # Line 2: Kind 2 (配列追加: requests にターン 0 を追加)
    line2 = json.dumps({
        "kind": 2,
        "k": ["requests"],
        "v": [{
            "requestId": "req-001",
            "timestamp": 1775278275000,
            "message": "Please refactor the user login in auth.py and config.yaml",
            "agent": {
                "id": "github.copilot.editsAgent",
                "extensionDisplayName": "GitHub Copilot Chat"
            },
            "response": [
                {"value": "I updated `src/auth.py` and reviewed `config.yaml` for security."},
                {"toolUse": {"name": "apply_patch", "input": {"file": "src/auth.py"}}}
            ]
        }]
    })

    session_file.write_text(f"{line0}\n{line1}\n{line2}\n", encoding="utf-8")

    parser = CopilotDeltaSessionParser()
    events = parser.parse_session_file(session_file)

    assert len(events) == 1
    ev = events[0]

    assert ev.client_tool == ClientToolType.COPILOT
    assert ev.extraction_method == "retro_local_discovery"
    assert "source:github-copilot" in ev.tags
    assert "extraction:retroactive" in ev.tags
    assert "session:sess-copilot-test-01" in ev.tags
    assert "agent:github.copilot.editsAgent" in ev.tags

    # プロベナンス検証
    assert ev.forensic_provenance is not None
    assert ev.forensic_provenance.parser_id == "copilot-delta-v1"
    assert len(ev.forensic_provenance.source_sha256) == 64

    # プロンプト検証
    assert "Please refactor the user login in auth.py" in ev.trigger.sanitized_prompt

    # ツール呼出・言及ファイル検証
    assert len(ev.tool_calls) == 1
    assert ev.tool_calls[0].tool_name == "apply_patch"
    assert any("auth.py" in f for f in ev.affected_files)
    assert any("config.yaml" in f for f in ev.affected_files)


def test_copilot_delta_parser_sensitive_redaction(tmp_path: Path):
    """プロンプト内に埋め込まれたシークレットが抽出時に自動マスキングされることを検証"""
    session_file = tmp_path / "copilot_secret_session.jsonl"

    raw_content = json.dumps({
        "kind": 0,
        "v": {
            "sessionId": "sess-secret",
            "creationDate": 1775278274000,
            "requests": [{
                "requestId": "req-secret",
                "timestamp": 1775278274500,
                "message": "Use this key sk-proj-1234567890abcdef1234567890abcdef1234567890 for API calls",
                "response": []
            }]
        }
    })
    session_file.write_text(raw_content + "\n", encoding="utf-8")

    parser = CopilotDeltaSessionParser()
    events = parser.parse_session_file(session_file)

    assert len(events) == 1
    sanitized = events[0].trigger.sanitized_prompt
    assert "sk-proj-1234567890" not in sanitized
    assert "[REDACTED_" in sanitized


def test_git_pr_correlator_scoring():
    """Git コミット多層相関スコア（時間・ファイル・PR）の判定ロジックを検証"""
    correlator = GitPRCorrelator(repo_path=Path("."))

    event_time = datetime(2026, 9, 13, 10, 0, 0)
    event = NormalizedAIEvent(
        trace_id="test-trace",
        timestamp=event_time,
        client_tool=ClientToolType.COPILOT,
        trigger=NormalizedTrigger(
            source=TriggerSourceType.CHAT_PROMPT,
            sanitized_prompt="Implement secure password hashing in security.py",
            user_identity="test-user",
            session_id="sess-001"
        ),
        affected_files=["src/security.py", "tests/test_security.py"]
    )

    # 1. 20分後の高相関コミット (ファイル完全一致 + PR #42 付与)
    good_commit = GitCommitMetadata(
        commit_sha="a1b2c3d4e5f6071829304152637485960718293a",
        timestamp=event_time + timedelta(minutes=20),
        author="Alice",
        message="feat: implement secure password hashing (#42)",
        changed_files=["src/security.py", "tests/test_security.py"],
        pr_number=42,
        pr_url="https://github.com/pull/42"
    )

    # 2. 5日前の無関係なコミット
    unrelated_commit = GitCommitMetadata(
        commit_sha="f9e8d7c6b5a4132435465768798091a2b3c4d5e6",
        timestamp=event_time - timedelta(days=5),
        author="Bob",
        message="docs: update readme styling",
        changed_files=["README.md"]
    )

    ctx = correlator.correlate_event(event, commits=[unrelated_commit, good_commit])

    assert ctx.commit_sha == good_commit.commit_sha
    assert ctx.confidence_level == "HIGH"
    assert ctx.confidence_score >= 0.65
    assert ctx.pr_number == 42
    assert "score:" in (ctx.correlation_proof or "")


def test_retro_auditor_end_to_end(tmp_path: Path):
    """探索から抽出、相関、WAL/ハッシュチェーン集積、完全性検証までの一連フローを検証"""
    repo_dir = tmp_path / "mock_repo"
    repo_dir.mkdir()

    # 擬似セッションファイルを作成
    session_file = tmp_path / "sample_copilot.jsonl"
    session_data = json.dumps({
        "kind": 0,
        "v": {
            "sessionId": "mock-session-999",
            "creationDate": 1775278274000,
            "requests": [{
                "requestId": "r-1",
                "timestamp": 1775278274100,
                "message": "fix edge case in parser",
                "response": [{"value": "Fixed edge case in `parser.py`"}]
            }]
        }
    })
    session_file.write_text(session_data + "\n", encoding="utf-8")

    auditor = RetroactiveSessionAuditor(repo_path=repo_dir)

    # ディスカバリーをモック化して一時ファイルを探索結果とする
    mock_target = DiscoveryTarget(
        client_tool="github-copilot",
        file_path=session_file,
        workspace_uri=str(repo_dir),
        is_matched_workspace=True,
        last_modified=datetime.utcnow(),
        size_bytes=session_file.stat().st_size
    )

    log_file = tmp_path / "audit-trail.jsonl"
    with patch.object(LocalStorageDiscoverer, "discover_all", return_value=[mock_target]):
        report = auditor.run_audit(
            tool_filter="all",
            correlate_git=False,  # mock repo には git commit がないため
            ingest=True,
            log_file_path=log_file
        )

    assert report.discovered_files_count == 1
    assert report.extracted_events_count == 1
    assert report.ingested_wal_count == 1
    assert report.ingested_audit_trail_count == 1

    # ログファイルの暗号学的完全性を検証
    assert log_file.exists()
    success, count, err = HashChainManager.verify_log_file(str(log_file))
    assert success is True
    assert count == 1
    assert err is None
