"""
Unit tests for MicroChainManager
Verifies session-scoped hash chaining, deterministic integrity, and tamper detection.
"""
import copy
import pytest
from aegis.archivist.integrity import MicroChainManager


def test_micro_chain_normal_flow():
    session_id = "sess-alpha-1234"
    manager = MicroChainManager(session_id)

    raw_events = [
        {"action": "turn_1", "prompt": "Hello AI"},
        {"action": "tool_call", "command": "git status"},
        {"action": "turn_2", "prompt": "Show results"},
    ]

    signed_events = []
    for ev in raw_events:
        signed = manager.sign_event(dict(ev))
        signed_events.append(signed)

    assert len(signed_events) == 3
    # 各イベントの integrity フィールド確認
    for idx, ev in enumerate(signed_events):
        assert ev["integrity"]["session_id"] == session_id
        assert ev["integrity"]["sequence_index"] == idx
        assert "previous_record_hash" in ev["integrity"]
        assert "current_record_hash" in ev["integrity"]

    # 1番目の直前ハッシュは Genesis Hash
    assert signed_events[0]["integrity"]["previous_record_hash"] == manager.genesis_hash
    # 2番目の直前ハッシュは 1番目の現在ハッシュ
    assert (
        signed_events[1]["integrity"]["previous_record_hash"]
        == signed_events[0]["integrity"]["current_record_hash"]
    )
    # 3番目の直前ハッシュは 2番目の現在ハッシュ
    assert (
        signed_events[2]["integrity"]["previous_record_hash"]
        == signed_events[1]["integrity"]["current_record_hash"]
    )

    # 整合性検証
    valid, count, error = MicroChainManager.verify_event_stream(session_id, signed_events)
    assert valid is True
    assert count == 3
    assert error is None


def test_micro_chain_tamper_payload():
    """ペイロードの改ざん検知テスト"""
    session_id = "sess-beta-5678"
    manager = MicroChainManager(session_id)

    events = [
        manager.sign_event({"step": 1, "code": "print('ok')"}),
        manager.sign_event({"step": 2, "code": "run_test()"}),
    ]

    # 改ざんなし
    valid, _, _ = MicroChainManager.verify_event_stream(session_id, events)
    assert valid is True

    # 1文字改ざん
    tampered_events = copy.deepcopy(events)
    tampered_events[1]["code"] = "run_test_tampered()"

    valid, failed_idx, error = MicroChainManager.verify_event_stream(session_id, tampered_events)
    assert valid is False
    assert failed_idx == 1
    assert "Tampering at index 1" in error


def test_micro_chain_tamper_reorder():
    """イベント順序の入れ替え検知テスト"""
    session_id = "sess-gamma-9999"
    manager = MicroChainManager(session_id)

    e1 = manager.sign_event({"step": 1})
    e2 = manager.sign_event({"step": 2})

    reordered = [e2, e1]
    valid, failed_idx, error = MicroChainManager.verify_event_stream(session_id, reordered)
    assert valid is False
    assert failed_idx == 0
    assert "Sequence mismatch" in error
