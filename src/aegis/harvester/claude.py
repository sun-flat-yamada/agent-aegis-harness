"""
Claude Code Local Session JSONL Parser & Normalizer
Parses session files from ~/.claude/projects/ and converts them to NormalizedAIEvent.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from aegis.models import (
    ClientToolType,
    NormalizedAIEvent,
    NormalizedInference,
    NormalizedToolCall,
    NormalizedTrigger,
    TriggerSourceType,
)
from aegis.sentinel.redactor import SensitiveRedactor


class ClaudeSessionParser:
    """Claude Code のローカルセッション JSONL ファイルのパーサー"""

    def __init__(self):
        self.redactor = SensitiveRedactor()

    def parse_session_file(self, file_path: Path) -> List[NormalizedAIEvent]:
        """JSONL ファイル全体を読み込み、監査イベントのリストへ変換"""
        events = []
        if not file_path.exists():
            return events

        with file_path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    event = self.normalize_record(record, session_id=file_path.stem)
                    if event:
                        events.append(event)
                except Exception:
                    continue
        return events

    def normalize_record(self, raw_record: Dict[str, Any], session_id: str = "claude-session") -> Optional[NormalizedAIEvent]:
        """単一の JSONL レコードを NormalizedAIEvent へ変換"""
        msg_type = raw_record.get("type")
        if not msg_type:
            return None

        # ユーザープロンプト
        if msg_type == "user":
            raw_text = str(raw_record.get("message", {}).get("content", ""))
            sanitized, _ = self.redactor.redact_text(raw_text)
            return NormalizedAIEvent(
                trace_id=raw_record.get("session_id", session_id),
                client_tool=ClientToolType.CLAUDE_CODE,
                trigger=NormalizedTrigger(
                    source=TriggerSourceType.CHAT_PROMPT,
                    sanitized_prompt=sanitized,
                    user_identity="local-user",
                    session_id=session_id
                )
            )

        # アシスタント思考・ツール実行
        elif msg_type == "assistant":
            content_blocks = raw_record.get("message", {}).get("content", [])
            thinking_texts = []
            tool_calls = []

            for b in content_blocks:
                if isinstance(b, dict):
                    if b.get("type") == "thinking":
                        thinking_texts.append(b.get("thinking", ""))
                    elif b.get("type") == "tool_use":
                        tool_calls.append(
                            NormalizedToolCall(
                                tool_name=b.get("name", "unknown_tool"),
                                arguments=b.get("input", {}),
                                status="SUCCESS"
                            )
                        )

            thinking_summary = " ".join(thinking_texts)[:500] if thinking_texts else None
            return NormalizedAIEvent(
                trace_id=raw_record.get("session_id", session_id),
                client_tool=ClientToolType.CLAUDE_CODE,
                trigger=NormalizedTrigger(
                    source=TriggerSourceType.CHAT_PROMPT,
                    sanitized_prompt="[assistant response]",
                    user_identity="claude-agent",
                    session_id=session_id
                ),
                inference=NormalizedInference(
                    chain_of_thought_summary=thinking_summary,
                    user_intent_summary=thinking_summary
                ),
                tool_calls=tool_calls
            )

        return None
