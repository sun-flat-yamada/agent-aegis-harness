"""
Unit tests for Aegis Write-Ahead Log (WAL) Buffer
Verifies ultra-low latency persistence, batch operations, and concurrency under thread stress.
"""
import concurrent.futures
import tempfile
from pathlib import Path

import pytest
from aegis.recorder.wal import AegisWALBuffer


def test_wal_enqueue_and_fetch():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_wal.db"
        wal = AegisWALBuffer(db_path)

        assert wal.get_pending_count() == 0
        assert wal.get_total_count() == 0

        # イベントのエンキュー
        event1 = {
            "trace_id": "trace-001",
            "integrity": {"session_id": "session-A", "sequence_index": 0},
            "data": "first event",
        }
        event2 = {
            "trace_id": "trace-002",
            "integrity": {"session_id": "session-A", "sequence_index": 1},
            "data": "second event",
        }

        id1 = wal.enqueue(event1)
        id2 = wal.enqueue(event2)

        assert id1 > 0
        assert id2 > id1
        assert wal.get_pending_count() == 2
        assert wal.get_total_count() == 2

        # バッチ取得
        pending = wal.fetch_pending(limit=10)
        assert len(pending) == 2
        assert pending[0][0] == id1
        assert pending[0][1]["trace_id"] == "trace-001"
        assert pending[1][0] == id2
        assert pending[1][1]["trace_id"] == "trace-002"

        # 送信完了マーク
        wal.mark_sent([id1])
        assert wal.get_pending_count() == 1
        assert wal.get_total_count() == 2

        # パージ処理
        wal.purge_sent(keep_last=0)
        assert wal.get_total_count() == 1
        assert wal.get_pending_count() == 1


def test_wal_concurrency():
    """マルチスレッドからの並行書き込みでロック競合エラーが発生しないことを検証"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "concurrent_wal.db"
        wal = AegisWALBuffer(db_path)

        num_threads = 10
        events_per_thread = 30
        total_events = num_threads * events_per_thread

        def worker(thread_idx: int):
            for seq in range(events_per_thread):
                event = {
                    "trace_id": f"trace-{thread_idx}-{seq}",
                    "integrity": {
                        "session_id": f"session-{thread_idx}",
                        "sequence_index": seq,
                    },
                    "data": f"Thread {thread_idx} event {seq}",
                }
                wal.enqueue(event)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            concurrent.futures.wait(futures)
            for f in futures:
                f.result()  # 例外があれば raise される

        assert wal.get_total_count() == total_events
        assert wal.get_pending_count() == total_events
