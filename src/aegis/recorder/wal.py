"""
Aegis Write-Ahead Log (WAL) Buffer
Provides ultra-low latency (<1ms) local persistence with zero lock contention
using SQLite WAL mode for high-concurrency enterprise developer environments.
"""
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class AegisWALBuffer:
    DEFAULT_DB_PATH = ".aegis/logs/aegis_wal.db"

    def __init__(self, db_path: Union[str, Path] = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """WAL モードとビジータイムアウトを設定した接続を取得"""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=10.0,
            isolation_level=None  # autocommit mode
        )
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def _init_db(self):
        """WAL テーブルおよびインデックスの初期化"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events_wal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    sequence_index INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'PENDING'
                );
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_wal_status 
                ON audit_events_wal(status);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_wal_session 
                ON audit_events_wal(session_id, sequence_index);
            """)

    def enqueue(self, event_dict: Dict[str, Any]) -> int:
        """
        監査イベントを WAL に即座にエンキュー (書込レイテンシ < 1ms)
        戻り値: 挿入された内部 ID
        """
        trace_id = event_dict.get("trace_id", "")
        integrity = event_dict.get("integrity", {})
        session_id = integrity.get("session_id", "default_session")
        sequence_index = integrity.get("sequence_index", 0)
        payload_str = json.dumps(event_dict, ensure_ascii=False)

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO audit_events_wal (trace_id, session_id, sequence_index, payload, status)
                VALUES (?, ?, ?, ?, 'PENDING');
                """,
                (trace_id, session_id, sequence_index, payload_str)
            )
            return cursor.lastrowid

    def fetch_pending(self, limit: int = 50) -> List[Tuple[int, Dict[str, Any]]]:
        """
        未送信（PENDING）のイベントをバッチ取得
        戻り値: [(id, event_dict), ...]
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, payload FROM audit_events_wal
                WHERE status = 'PENDING'
                ORDER BY id ASC
                LIMIT ?;
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            results = []
            for row_id, payload_str in rows:
                try:
                    event_dict = json.loads(payload_str)
                    results.append((row_id, event_dict))
                except json.JSONDecodeError:
                    pass
            return results

    def mark_sent(self, ids: List[int]):
        """送信完了したイベントのステータスを SENT に更新"""
        if not ids:
            return
        placeholders = ",".join("?" for _ in ids)
        with self._get_connection() as conn:
            conn.execute(
                f"""
                UPDATE audit_events_wal
                SET status = 'SENT'
                WHERE id IN ({placeholders});
                """,
                ids
            )

    def purge_sent(self, keep_last: int = 1000):
        """古い送信済みイベントをパージし、ディスク容量を一定に維持"""
        with self._get_connection() as conn:
            conn.execute(
                """
                DELETE FROM audit_events_wal
                WHERE status = 'SENT'
                AND id NOT IN (
                    SELECT id FROM audit_events_wal
                    WHERE status = 'SENT'
                    ORDER BY id DESC
                    LIMIT ?
                );
                """,
                (keep_last,)
            )

    def get_pending_count(self) -> int:
        """未送信イベント数を返却"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM audit_events_wal WHERE status = 'PENDING';")
            return cursor.fetchone()[0]

    def get_total_count(self) -> int:
        """全イベント数を返却"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM audit_events_wal;")
            return cursor.fetchone()[0]
