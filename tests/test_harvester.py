"""
Tests for Claude Session Parser and Harvester
"""
import pytest
from pathlib import Path
from aegis.harvester.claude import ClaudeSessionParser
from aegis.models import ClientToolType


def test_claude_session_parser_user_prompt(tmp_path: Path):
    """ユーザープロンプトが正しく NormalizedAIEvent に変換されることを検証"""
    session_file = tmp_path / "session-001.jsonl"
    line_user = '{"type": "user", "session_id": "sess-123", "message": {"content": "refactor authentication module"}}\n'
    session_file.write_text(line_user, encoding="utf-8")

    parser = ClaudeSessionParser()
    events = parser.parse_session_file(session_file)

    assert len(events) == 1
    assert events[0].client_tool == ClientToolType.CLAUDE_CODE
    assert events[0].trigger.sanitized_prompt == "refactor authentication module"
    assert events[0].trace_id == "sess-123"


def test_claude_session_parser_assistant_thinking_and_tool(tmp_path: Path):
    """アシスタントの思考ブロックおよびツール呼出が抽出されることを検証"""
    session_file = tmp_path / "session-002.jsonl"
    line_assistant = (
        '{"type": "assistant", "session_id": "sess-456", "message": {"content": ['
        '{"type": "thinking", "thinking": "We need to read the config file first."},'
        '{"type": "tool_use", "name": "read_file", "input": {"path": ".aegis/config.yaml"}}'
        ']}}\n'
    )
    session_file.write_text(line_assistant, encoding="utf-8")

    parser = ClaudeSessionParser()
    events = parser.parse_session_file(session_file)

    assert len(events) == 1
    ev = events[0]
    assert ev.client_tool == ClientToolType.CLAUDE_CODE
    assert "We need to read the config file first." in (ev.inference.chain_of_thought_summary or "")
    assert len(ev.tool_calls) == 1
    assert ev.tool_calls[0].tool_name == "read_file"
    assert ev.tool_calls[0].arguments == {"path": ".aegis/config.yaml"}
