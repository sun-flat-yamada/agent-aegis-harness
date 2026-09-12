"""
Azure Audit Exporter
Spools uncommitted audit events from local SQLite WAL and exports them to
Azure Event Hubs and Blob WORM Immutable Storage.
"""
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from aegis.models import AzureFullConfig
from aegis.recorder.wal import AegisWALBuffer

logger = logging.getLogger(__name__)


class AzureAuditExporter:
    def __init__(
        self,
        config: AzureFullConfig,
        wal_buffer: Optional[AegisWALBuffer] = None,
        transport_sender: Optional[Callable[[List[Dict[str, Any]]], bool]] = None,
    ):
        self.config = config
        self.wal = wal_buffer or AegisWALBuffer()
        # テストや外部差し替えが可能なトランスポート関数 (デフォルトはモックまたは HTTP 送信)
        self.sender = transport_sender or self._default_sender

    def _default_sender(self, events: List[Dict[str, Any]]) -> bool:
        """
        デフォルトの送信処理。
        OTLP または Event Hubs REST API へのバッチ送信を行う (実装スタブ)。
        """
        if not events:
            return True
        logger.info(f"Exported {len(events)} events to Azure Event Hub '{self.config.event_hubs_name}'")
        return True

    def export_batch(self, batch_size: int = 50) -> Tuple[int, int]:
        """
        WAL から未送信イベントを取得して Azure へバッチ送信。
        戻り値: (送信成功件数, 残存未送信件数)
        """
        pending_items = self.wal.fetch_pending(limit=batch_size)
        if not pending_items:
            return 0, self.wal.get_pending_count()

        row_ids = [item[0] for item in pending_items]
        event_dicts = [item[1] for item in pending_items]

        success = False
        try:
            success = self.sender(event_dicts)
        except Exception as e:
            logger.error(f"Failed to export batch to Azure: {e}")
            success = False

        if success:
            self.wal.mark_sent(row_ids)
            return len(row_ids), self.wal.get_pending_count()
        else:
            return 0, self.wal.get_pending_count()
