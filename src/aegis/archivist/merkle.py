"""
Merkle Tree Batch Sealing Engine for Agent Aegis Harness
Builds deterministic binary Merkle trees from batches of Micro-Chain audit events,
calculates Merkle Roots for anchor notarization, and generates/verifies Merkle Proofs.
"""
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from aegis.models import MerkleProof


class MerkleTreeSealer:
    """
    Constructs a binary Merkle Tree over a batch of event hashes.
    Provides logarithmic-time Proof of Inclusion (Merkle Proof).
    """

    def __init__(self, leaf_hashes: List[str], batch_id: Optional[str] = None):
        if not leaf_hashes:
            raise ValueError("leaf_hashes cannot be empty to construct a Merkle Tree")
        
        self.original_leaves = list(leaf_hashes)
        self.batch_id = batch_id or f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.batch_timestamp = datetime.utcnow()
        self.levels: List[List[str]] = []
        self._build_tree()

    @staticmethod
    def hash_pair(left: str, right: str) -> str:
        """2つのハッシュを結合して SHA-256 を算出"""
        return hashlib.sha256((left + right).encode("utf-8")).hexdigest()

    def _build_tree(self):
        """ボトムアップで二分木ハッシュを再帰構築"""
        current_level = list(self.original_leaves)
        self.levels.append(current_level)

        while len(current_level) > 1:
            next_level = []
            # 奇数個の場合、末尾を複製して偶数にする
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])

            for i in range(0, len(current_level), 2):
                parent = self.hash_pair(current_level[i], current_level[i + 1])
                next_level.append(parent)

            self.levels.append(next_level)
            current_level = next_level

    @property
    def merkle_root(self) -> str:
        """二分木の頂点 (Merkle Root) を返却"""
        return self.levels[-1][0]

    def generate_proof(self, leaf_index: int) -> MerkleProof:
        """
        指定インデックスのリーフに対する兄弟ハッシュパス (Audit Path) を抽出
        """
        if leaf_index < 0 or leaf_index >= len(self.original_leaves):
            raise IndexError(f"leaf_index {leaf_index} out of bounds (total: {len(self.original_leaves)})")

        audit_path: List[str] = []
        current_index = leaf_index

        # 最下層からルートの直前層まで兄弟ノードを収集
        for level in self.levels[:-1]:
            # 奇数要素で補正されたレベル長を考慮
            level_len = len(level)
            if level_len % 2 != 0:
                # 最後の要素の兄弟は自分自身（複製）
                pass

            if current_index % 2 == 0:
                sibling_index = current_index + 1
                if sibling_index >= len(level):
                    # 自分が末尾で複製された場合、兄弟は自分自身
                    sibling_hash = level[current_index]
                else:
                    sibling_hash = level[sibling_index]
            else:
                sibling_index = current_index - 1
                sibling_hash = level[sibling_index]

            audit_path.append(sibling_hash)
            current_index //= 2

        return MerkleProof(
            batch_id=self.batch_id,
            batch_timestamp=self.batch_timestamp,
            leaf_index=leaf_index,
            total_leaves=len(self.original_leaves),
            merkle_root=self.merkle_root,
            audit_path=audit_path,
        )

    @classmethod
    def verify_proof(cls, leaf_hash: str, proof: MerkleProof) -> Tuple[bool, Optional[str]]:
        """
        リーフハッシュと MerkleProof からルートハッシュを再計算して照合
        戻り値: (検証成功フラグ, エラーメッセージ)
        """
        current_hash = leaf_hash
        current_index = proof.leaf_index

        for sibling in proof.audit_path:
            if current_index % 2 == 0:
                current_hash = cls.hash_pair(current_hash, sibling)
            else:
                current_hash = cls.hash_pair(sibling, current_hash)
            current_index //= 2

        if current_hash != proof.merkle_root:
            return (
                False,
                f"Merkle Root mismatch: computed '{current_hash}', expected '{proof.merkle_root}'"
            )

        return True, None
