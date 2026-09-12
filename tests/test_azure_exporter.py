"""
Unit tests for AzureAuditExporter
Verifies batch spooling from WAL to Azure transport, success commits, and failure rollbacks.
"""
import tempfile
from pathlib import Path
import pytest
from aegis.models import AzureFullConfig
from aegis.recorder.azure_exporter import AzureAuditExporter
from aegis.recorder.wal import AegisWALBuffer


def test_azure_exporter_batch_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "wal_test.db"
        wal = AegisWALBuffer(db_path)

        # 3件エンキュー
        for i in range(3):
            wal.enqueue({
                "trace_id": f"tr-{i}",
                "integrity": {"session_id": "sess-1", "sequence_index": i},
                "msg": f"event_{i}",
            })

        assert wal.get_pending_count() == 3

        config = AzureFullConfig(
            blob_account_name="staegistest",
            blob_container="aegis-worm",
        )

        sent_events = []
        def mock_sender(events):
            sent_events.extend(events)
            return True

        exporter = AzureAuditExporter(config=config, wal_buffer=wal, transport_sender=mock_sender)

        # バッチ送信実行
        exported_count, remaining = exporter.export_batch(batch_size=10)

        assert exported_count == 3
        assert remaining == 0
        assert wal.get_pending_count() == 0
        assert len(sent_events) == 3


def test_azure_exporter_batch_failure_retry():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "wal_retry.db"
        wal = AegisWALBuffer(db_path)

        wal.enqueue({"trace_id": "tr-fail", "integrity": {"session_id": "s", "sequence_index": 0}})
        assert wal.get_pending_count() == 1

        config = AzureFullConfig(
            blob_account_name="staegistest",
            blob_container="aegis-worm",
        )

        def failing_sender(events):
            raise ConnectionError("Network unreachable")

        exporter = AzureAuditExporter(config=config, wal_buffer=wal, transport_sender=failing_sender)

        exported_count, remaining = exporter.export_batch(batch_size=10)

        assert exported_count == 0
        assert remaining == 1
        assert wal.get_pending_count() == 1  # 送信失敗時は未送信のまま保持
