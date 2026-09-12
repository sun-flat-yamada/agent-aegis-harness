"""
Session Harvester Watcher Daemon
Monitors local session files and ingests normalized AI audit events into WAL.
"""
from pathlib import Path
from typing import List, Optional
from aegis.harvester.claude import ClaudeSessionParser
from aegis.recorder.wal import SQLiteWALStore


class SessionHarvester:
    """ローカルファイル変更を監視して AI 監査ログを自動収集するハーベスター"""

    def __init__(self, watch_dir: Optional[Path] = None):
        self.watch_dir = watch_dir or (Path.home() / ".claude" / "projects")
        self.parser = ClaudeSessionParser()
        self.wal = SQLiteWALStore()

    def scan_once(self) -> int:
        """監視ディレクトリを一回スキャンし、検出された新規イベントを WAL に取り込む"""
        ingested_count = 0
        if not self.watch_dir.exists():
            return 0

        # sessions/*.jsonl を検索
        jsonl_files = list(self.watch_dir.glob("**/sessions/*.jsonl"))
        for jf in jsonl_files:
            events = self.parser.parse_session_file(jf)
            for ev in events:
                try:
                    self.wal.append_event({
                        "trace_id": ev.trace_id,
                        "timestamp": ev.timestamp.isoformat(),
                        "tool_name": ev.client_tool.value,
                        "status": "INGESTED",
                        "summary": ev.trigger.sanitized_prompt[:100]
                    })
                    ingested_count += 1
                except Exception:
                    pass
        return ingested_count
