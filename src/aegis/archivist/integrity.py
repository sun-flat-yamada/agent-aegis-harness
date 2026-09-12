"""
Hash Chain Integrity Engine for Agent Aegis Harness
Provides cryptographic proof of log immutability and tamper detection
"""
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

class HashChainManager:
    GENESIS_HASH = "0" * 64

    @staticmethod
    def calculate_record_hash(record_data: Dict[str, Any], previous_hash: str) -> str:
        """
        直前のハッシュと現在の監査ペイロード（integrityフィールドを除く）から
        決定論的 SHA-256 ハッシュを算出
        """
        canonical_payload = {k: v for k, v in record_data.items() if k != "integrity"}
        canonical_payload["previous_record_hash"] = previous_hash
        
        # キーの昇順ソートで決定論的シリアライズ
        serialized = json.dumps(
            canonical_payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def sign_record(cls, record_dict: Dict[str, Any], previous_hash: str) -> Dict[str, Any]:
        """
        レコードに previous_record_hash と計算された current_record_hash を付与して署名
        """
        current_hash = cls.calculate_record_hash(record_dict, previous_hash)
        record_dict["integrity"] = {
            "previous_record_hash": previous_hash,
            "current_record_hash": current_hash,
        }
        return record_dict

    @classmethod
    def verify_log_file(cls, log_path: Union[str, Path]) -> Tuple[bool, int, Optional[str]]:
        """
        ログファイル全体の Hash Chain 整合性を検証
        戻り値: (成功フラグ, 検証した行数, エラーメッセージ)
        """
        path = Path(log_path)
        if not path.exists():
            return False, 0, f"Log file not found: {log_path}"

        expected_prev_hash = cls.GENESIS_HASH
        line_number = 0

        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line_number += 1
                line = raw_line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    return False, line_number, f"Invalid JSON at line {line_number}: {e}"

                integrity = record.get("integrity")
                if not integrity:
                    return False, line_number, f"Missing 'integrity' field at line {line_number}"

                recorded_prev = integrity.get("previous_record_hash")
                recorded_curr = integrity.get("current_record_hash")

                # 1. 前ブロックハッシュの連続性チェック
                if recorded_prev != expected_prev_hash:
                    return (
                        False,
                        line_number,
                        f"Broken chain link at line {line_number}: expected prev '{expected_prev_hash}', got '{recorded_prev}'"
                    )

                # 2. 現在ブロックハッシュの再計算・照合
                computed_curr = cls.calculate_record_hash(record, recorded_prev)
                if computed_curr != recorded_curr:
                    return (
                        False,
                        line_number,
                        f"Tampering detected at line {line_number}: computed '{computed_curr}', recorded '{recorded_curr}'"
                    )

                expected_prev_hash = recorded_curr

        return True, line_number, None


class MicroChainManager:
    """
    Session-scoped lightweight Hash Chain Manager.
    Eliminates cross-user/cross-process lock contention and Git conflicts
    by maintaining an isolated micro-chain per session.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        # セッション固有の Genesis Hash
        self.genesis_hash = hashlib.sha256(f"MICRO_GENESIS_{session_id}".encode("utf-8")).hexdigest()
        self.last_hash = self.genesis_hash
        self.sequence_index = 0

    def calculate_hash(self, payload: Dict[str, Any], previous_hash: str) -> str:
        """正規化されたペイロードと直前ハッシュから SHA-256 を算出"""
        canonical_payload = {k: v for k, v in payload.items() if k != "integrity"}
        canonical_payload["previous_micro_hash"] = previous_hash
        canonical_payload["session_id"] = self.session_id
        canonical_payload["sequence_index"] = self.sequence_index

        serialized = json.dumps(
            canonical_payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def sign_event(self, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """イベントにセッション局所連鎖署名を付与"""
        current_hash = self.calculate_hash(event_dict, self.last_hash)
        event_dict["integrity"] = {
            "session_id": self.session_id,
            "sequence_index": self.sequence_index,
            "previous_record_hash": self.last_hash,
            "current_record_hash": current_hash,
        }
        self.last_hash = current_hash
        self.sequence_index += 1
        return event_dict

    @classmethod
    def verify_event_stream(cls, session_id: str, events: list[Dict[str, Any]]) -> Tuple[bool, int, Optional[str]]:
        """セッション内の一連のイベント列の Micro-Chain 整合性を検証"""
        expected_prev = hashlib.sha256(f"MICRO_GENESIS_{session_id}".encode("utf-8")).hexdigest()
        manager = cls(session_id)

        for idx, event in enumerate(events):
            integrity = event.get("integrity", {})
            recorded_prev = integrity.get("previous_record_hash")
            recorded_curr = integrity.get("current_record_hash")
            recorded_seq = integrity.get("sequence_index")

            if recorded_seq != idx:
                return False, idx, f"Sequence mismatch at index {idx}: expected {idx}, got {recorded_seq}"

            if recorded_prev != expected_prev:
                return False, idx, f"Broken link at index {idx}: expected prev {expected_prev}, got {recorded_prev}"

            manager.sequence_index = idx
            computed = manager.calculate_hash(event, recorded_prev)
            if computed != recorded_curr:
                return False, idx, f"Tampering at index {idx}: computed {computed}, recorded {recorded_curr}"

            expected_prev = recorded_curr

        return True, len(events), None


class MerkleProofVerifier:
    """
    Convenience verifier for Layer 2 Merkle Batch Proofs.
    """
    @staticmethod
    def verify(leaf_hash: str, proof: Any) -> Tuple[bool, Optional[str]]:
        from aegis.archivist.merkle import MerkleTreeSealer
        return MerkleTreeSealer.verify_proof(leaf_hash, proof)

