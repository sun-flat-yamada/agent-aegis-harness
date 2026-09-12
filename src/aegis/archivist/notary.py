"""
Audit Notary & Anchor Engine
Manages notarization headers, chains batch Merkle Roots into an immutable ledger,
and prepares payload for public git notarization (GitHub aegis-audit-ledger).
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class AuditNotary:
    GENESIS_NOTARY_HASH = "0" * 64
    DEFAULT_LEDGER_PATH = ".aegis/logs/merkle_ledger.jsonl"

    def __init__(self, ledger_path: Union[str, Path] = DEFAULT_LEDGER_PATH):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.last_batch_hash = self._get_latest_batch_hash()

    def _get_latest_batch_hash(self) -> str:
        """台帳ファイルから直前バッチの current_batch_hash を取得"""
        if not self.ledger_path.exists() or self.ledger_path.stat().st_size == 0:
            return self.GENESIS_NOTARY_HASH

        last_hash = self.GENESIS_NOTARY_HASH
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        curr = record.get("current_batch_hash")
                        if curr:
                            last_hash = curr
                    except Exception:
                        pass
        return last_hash

    @staticmethod
    def calculate_batch_hash(previous_batch_hash: str, merkle_root: str, timestamp_str: str) -> str:
        """直前バッチハッシュと Merkle Root から決定論的 SHA-256 を算出"""
        payload = f"{previous_batch_hash}:{merkle_root}:{timestamp_str}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def create_batch_header(
        self,
        batch_id: str,
        merkle_root: str,
        total_events: int,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        バッチ封印ヘッダーを生成し、直前バッチと暗号連鎖
        """
        ts = timestamp or datetime.utcnow()
        ts_str = ts.isoformat()
        current_hash = self.calculate_batch_hash(self.last_batch_hash, merkle_root, ts_str)

        header = {
            "batch_id": batch_id,
            "merkle_root": merkle_root,
            "total_events": total_events,
            "timestamp": ts_str,
            "previous_batch_hash": self.last_batch_hash,
            "current_batch_hash": current_hash,
            "metadata": metadata or {},
        }
        self.last_batch_hash = current_hash
        return header

    def commit_batch(self, header: Dict[str, Any]) -> Dict[str, Any]:
        """台帳ファイルにバッチヘッダーを追記永続化"""
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(header, ensure_ascii=False) + "\n")
        return header

    @classmethod
    def verify_ledger_file(cls, ledger_path: Union[str, Path]) -> Tuple[bool, int, Optional[str]]:
        """台帳ファイル全体の Merkle Root 連鎖整合性を検証"""
        path = Path(ledger_path)
        if not path.exists():
            return False, 0, f"Ledger file not found: {ledger_path}"

        expected_prev = cls.GENESIS_NOTARY_HASH
        count = 0

        with open(path, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                count += 1
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    return False, count, f"Invalid JSON at line {count}: {e}"

                prev = record.get("previous_batch_hash")
                curr = record.get("current_batch_hash")
                root = record.get("merkle_root")
                ts = record.get("timestamp")

                if prev != expected_prev:
                    return False, count, f"Broken link at line {count}: expected {expected_prev}, got {prev}"

                computed = cls.calculate_batch_hash(prev, root, ts)
                if computed != curr:
                    return False, count, f"Tampering at line {count}: computed {computed}, recorded {curr}"

                expected_prev = curr

        return True, count, None

    def export_git_anchor_payload(self, header: Dict[str, Any]) -> str:
        """GitHub コミットメッセージ / 公証ファイル用のマークダウン/テキスト表現を生成"""
        return (
            f"Aegis Merkle Anchor Seal: {header['batch_id']}\n\n"
            f"- Merkle Root: `{header['merkle_root']}`\n"
            f"- Total Events: {header['total_events']}\n"
            f"- Sealed At: {header['timestamp']}\n"
            f"- Previous Batch Hash: `{header['previous_batch_hash']}`\n"
            f"- Current Batch Hash: `{header['current_batch_hash']}`\n"
        )
