"""
Unit tests for Merkle Tree Batch Sealer and Audit Notary
Verifies binary Merkle tree construction, Merkle Proof generation/verification,
tamper detection, large scale performance, and Notary ledger chaining.
"""
import hashlib
import tempfile
import time
from pathlib import Path

import pytest
from aegis.archivist.integrity import MerkleProofVerifier
from aegis.archivist.merkle import MerkleTreeSealer
from aegis.archivist.notary import AuditNotary


def _dummy_hash(val: str) -> str:
    return hashlib.sha256(val.encode("utf-8")).hexdigest()


def test_merkle_tree_construction_even():
    leaves = [_dummy_hash(f"leaf_{i}") for i in range(4)]
    sealer = MerkleTreeSealer(leaves, batch_id="batch-even-001")

    assert sealer.merkle_root is not None
    assert len(sealer.merkle_root) == 64
    assert len(sealer.levels) == 3  # Level 0: 4, Level 1: 2, Level 2: 1

    # 各リーフの証明検証
    for idx, leaf in enumerate(leaves):
        proof = sealer.generate_proof(idx)
        assert proof.leaf_index == idx
        assert proof.total_leaves == 4
        assert proof.merkle_root == sealer.merkle_root
        valid, err = MerkleTreeSealer.verify_proof(leaf, proof)
        assert valid is True
        assert err is None


def test_merkle_tree_construction_odd():
    # 奇数個のリーフ (3個, 5個)
    for count in [3, 5, 7]:
        leaves = [_dummy_hash(f"leaf_{count}_{i}") for i in range(count)]
        sealer = MerkleTreeSealer(leaves, batch_id=f"batch-odd-{count}")

        for idx, leaf in enumerate(leaves):
            proof = sealer.generate_proof(idx)
            valid, err = MerkleTreeSealer.verify_proof(leaf, proof)
            assert valid is True, f"Failed for leaf {idx} in tree of {count} leaves: {err}"
            # MerkleProofVerifier 経由でも検証
            valid2, _ = MerkleProofVerifier.verify(leaf, proof)
            assert valid2 is True


def test_merkle_proof_tamper():
    leaves = [_dummy_hash(f"event_{i}") for i in range(8)]
    sealer = MerkleTreeSealer(leaves, batch_id="batch-tamper-test")

    proof_0 = sealer.generate_proof(0)

    # 1. 異なるリーフハッシュで検証
    fake_leaf = _dummy_hash("attacker_event")
    valid, err = MerkleTreeSealer.verify_proof(fake_leaf, proof_0)
    assert valid is False
    assert "Merkle Root mismatch" in err

    # 2. 兄弟ハッシュパスの改ざん
    tampered_proof = proof_0.model_copy(deep=True)
    tampered_proof.audit_path[0] = _dummy_hash("tampered_sibling")
    valid2, err2 = MerkleTreeSealer.verify_proof(leaves[0], tampered_proof)
    assert valid2 is False
    assert "Merkle Root mismatch" in err2


def test_merkle_large_scale_performance():
    """1,000 件のイベントから高速に Merkle Tree を構築し、証明を検証 (< 100ms)"""
    leaves = [_dummy_hash(f"scale_event_{i}") for i in range(1000)]

    start_time = time.time()
    sealer = MerkleTreeSealer(leaves, batch_id="batch-scale-1000")
    duration = time.time() - start_time

    assert duration < 0.2  # 200ms 以内 (通常は < 30ms)
    assert len(sealer.levels) == 11  # 1000 -> 500 -> 250 -> 125 -> 63 -> 32 -> 16 -> 8 -> 4 -> 2 -> 1

    # ランダムな位置の証明検証
    for test_idx in [0, 123, 456, 789, 999]:
        proof = sealer.generate_proof(test_idx)
        valid, err = MerkleTreeSealer.verify_proof(leaves[test_idx], proof)
        assert valid is True


def test_audit_notary_ledger():
    """AuditNotary のバッチヘッダー生成と暗号連鎖台帳の検証"""
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "merkle_ledger.jsonl"
        notary = AuditNotary(ledger_path)

        # 3つのバッチを順次コミット
        roots = [_dummy_hash(f"batch_root_{i}") for i in range(3)]
        for i, root in enumerate(roots):
            header = notary.create_batch_header(
                batch_id=f"batch_{i}",
                merkle_root=root,
                total_events=(i + 1) * 100,
            )
            notary.commit_batch(header)

        # 台帳全体の連鎖検証
        valid, count, err = AuditNotary.verify_ledger_file(ledger_path)
        assert valid is True
        assert count == 3
        assert err is None

        # 台帳の改ざん検知テスト
        content = ledger_path.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        # 2行目の root を改ざん
        import json
        row1 = json.loads(lines[1])
        row1["merkle_root"] = _dummy_hash("tampered_root")
        lines[1] = json.dumps(row1)
        ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        valid_tampered, failed_line, err_tampered = AuditNotary.verify_ledger_file(ledger_path)
        assert valid_tampered is False
        assert failed_line == 2
        assert "Tampering at line 2" in err_tampered
