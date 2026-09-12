"""
Tests for Aegis Archivist (Policy Hasher and Hash Chain Integrity)
"""
import json
import pytest
from pathlib import Path
from aegis.archivist.integrity import HashChainManager
from aegis.archivist.policy_hasher import PolicyHasher

def test_policy_hasher_deterministic(tmp_path):
    """ポリシーハッシュが同一内容に対して決定論的に同一の出力を返すことを検証"""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    
    rule1 = rules_dir / "rule1.yaml"
    rule1.write_text("rule_id: R1\nname: Test Rule\n", encoding="utf-8")
    
    hasher1 = PolicyHasher(target_dirs=[str(rules_dir)])
    digest1 = hasher1.compute_digest()
    
    hasher2 = PolicyHasher(target_dirs=[str(rules_dir)])
    digest2 = hasher2.compute_digest()
    
    assert digest1 == digest2
    assert digest1.startswith("sha256:")

def test_policy_hasher_detects_modification(tmp_path):
    """ルールファイルが1文字でも変更された場合にダイジェストが変わることを検証"""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    
    rule1 = rules_dir / "rule1.yaml"
    rule1.write_text("rule_id: R1\nname: Initial\n", encoding="utf-8")
    
    hasher = PolicyHasher(target_dirs=[str(rules_dir)])
    digest_before = hasher.compute_digest()
    
    # ファイルを変更
    rule1.write_text("rule_id: R1\nname: Modified\n", encoding="utf-8")
    digest_after = hasher.compute_digest()
    
    assert digest_before != digest_after

def test_hash_chain_signing_and_verification(tmp_path):
    """Hash Chain の署名とログ全体の完全性検証が正しく行われることを検証"""
    log_file = tmp_path / "audit-trail.jsonl"
    
    records = [
        {"step": 1, "action": "read_file", "path": "main.py"},
        {"step": 2, "action": "edit_file", "path": "main.py"},
        {"step": 3, "action": "test_run", "result": "PASS"},
    ]
    
    prev_hash = HashChainManager.GENESIS_HASH
    with open(log_file, "w", encoding="utf-8") as f:
        for rec in records:
            signed = HashChainManager.sign_record(rec, prev_hash)
            prev_hash = signed["integrity"]["current_record_hash"]
            f.write(json.dumps(signed) + "\n")
            
    # 検証
    success, count, err = HashChainManager.verify_log_file(log_file)
    assert success is True
    assert count == 3
    assert err is None

def test_hash_chain_tamper_detection(tmp_path):
    """ログファイル内の任意の1文字が改ざんされた場合、即座に検知されることを検証"""
    log_file = tmp_path / "audit-trail.jsonl"
    
    records = [
        {"step": 1, "action": "query", "user": "alice"},
        {"step": 2, "action": "execute", "cmd": "pytest"},
    ]
    
    prev_hash = HashChainManager.GENESIS_HASH
    with open(log_file, "w", encoding="utf-8") as f:
        for rec in records:
            signed = HashChainManager.sign_record(rec, prev_hash)
            prev_hash = signed["integrity"]["current_record_hash"]
            f.write(json.dumps(signed) + "\n")
            
    # 改ざん: 1行目の user を alice から mallory に書き換える
    lines = log_file.read_text(encoding="utf-8").splitlines()
    tampered_first_line = lines[0].replace('"alice"', '"mallory"')
    log_file.write_text(tampered_first_line + "\n" + lines[1] + "\n", encoding="utf-8")
    
    # 検証実行
    success, count, err = HashChainManager.verify_log_file(log_file)
    assert success is False
    assert "Tampering detected" in err or "Broken chain link" in err
