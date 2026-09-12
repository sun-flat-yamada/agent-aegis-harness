"""
Aegis Recorder & Tracer
Extracts 5W1H audit records and manages Dual-Stream logs (audit-trail & forensic-trail)
with SQLite WAL buffer and Session Micro-Chain integration.
"""
import json
import os
from pathlib import Path
from typing import Optional, Union

from aegis.archivist.integrity import HashChainManager, MicroChainManager
from aegis.models import AegisAuditEvent
from aegis.recorder.wal import AegisWALBuffer


class AegisRecorder:
    def __init__(
        self,
        audit_trail_path: Union[str, Path] = ".aegis/logs/audit-trail.jsonl",
        forensic_trail_path: Union[str, Path] = ".aegis/logs/forensic-trail.jsonl",
        enable_wal: bool = True,
        wal_db_path: Union[str, Path] = AegisWALBuffer.DEFAULT_DB_PATH,
        session_id: Optional[str] = None,
    ):
        self.audit_trail_path = Path(audit_trail_path)
        self.forensic_trail_path = Path(forensic_trail_path)
        self.enable_wal = enable_wal
        self.session_id = session_id or "default_session"

        # 親ディレクトリの存在を保証
        self.audit_trail_path.parent.mkdir(parents=True, exist_ok=True)
        self.forensic_trail_path.parent.mkdir(parents=True, exist_ok=True)

        self.audit_trail_last_hash = self._get_latest_hash(self.audit_trail_path)
        self.forensic_trail_last_hash = self._get_latest_hash(self.forensic_trail_path)

        # Micro-Chain & WAL 初期化
        self.micro_chain = MicroChainManager(self.session_id)
        self.wal = AegisWALBuffer(wal_db_path) if enable_wal else None

    @staticmethod
    def _get_latest_hash(path: Path) -> str:
        """指定されたログファイルから末尾レコードの current_record_hash を取得"""
        if not path.exists() or path.stat().st_size == 0:
            return HashChainManager.GENESIS_HASH

        last_valid_hash = HashChainManager.GENESIS_HASH
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        curr = record.get("integrity", {}).get("current_record_hash")
                        if curr:
                            last_valid_hash = curr
                    except Exception:
                        pass
        return last_valid_hash

    def record(self, event: AegisAuditEvent) -> AegisAuditEvent:
        """
        監査イベントを署名し、Dual-Stream および WAL バッファに永続化
        """
        event_dict = event.model_dump(mode="json")

        # 1. Forensic Trail には完全なペイロードを署名して記録
        signed_forensic = HashChainManager.sign_record(event_dict, self.forensic_trail_last_hash)
        self.forensic_trail_last_hash = signed_forensic["integrity"]["current_record_hash"]

        with open(self.forensic_trail_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(signed_forensic, ensure_ascii=False) + "\n")

        # 2. Audit Trail (軽量版) には主要ガバナンスメタデータ + forensic_record_hash を記録
        compact_dict = {
            "trace_id": signed_forensic["trace_id"],
            "span_id": signed_forensic["span_id"],
            "step_index": signed_forensic["step_index"],
            "timestamp": signed_forensic["timestamp"],
            "audit_reproducibility": signed_forensic["audit_reproducibility"],
            "environment": {
                "client_tool": signed_forensic["environment"]["client_tool"],
                "repository": signed_forensic["environment"]["repository"],
                "git_commit": signed_forensic["environment"]["git_commit"],
            },
            "trigger": {
                "source": signed_forensic["trigger"]["source"],
                "sanitized_prompt": signed_forensic["trigger"]["sanitized_prompt"][:200],
            },
            "forensic_record_hash": self.forensic_trail_last_hash,
            "sentinel_verdict": signed_forensic["sentinel_verdict"],
        }
        # compact_dict 自身も独立した Hash Chain で署名
        signed_compact = HashChainManager.sign_record(compact_dict, self.audit_trail_last_hash)
        self.audit_trail_last_hash = signed_compact["integrity"]["current_record_hash"]

        with open(self.audit_trail_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(signed_compact, ensure_ascii=False) + "\n")

        # 3. WAL バッファが有効な場合は即時エンキュー (セッション Micro-Chain 署名を付与)
        if self.wal:
            wal_event = dict(signed_forensic)
            wal_event = self.micro_chain.sign_event(wal_event)
            self.wal.enqueue(wal_event)

        # 署名済みイベントオブジェクトを再構築して返却
        return AegisAuditEvent.model_validate(signed_forensic)

    def flush(self):
        """バッファのフラッシュ処理"""
        pass

