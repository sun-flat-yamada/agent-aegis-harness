"""
Tests for Aegis Refiner (ClusterAnalyzer and PatchProposer)
"""
import json
import pytest
from pathlib import Path
from aegis.refiner.cluster_analyzer import ClusterAnalyzer, AuditClusterSummary
from aegis.refiner.patch_proposer import PatchProposer

def test_cluster_analyzer_empty_log(tmp_path):
    """ログファイルが存在しない、または空の場合の正常系ハンドリング"""
    log_file = tmp_path / "empty.jsonl"
    analyzer = ClusterAnalyzer(log_path=log_file)
    summary = analyzer.analyze()
    assert summary.total_events == 0
    assert summary.pass_count == 0
    assert summary.avg_score == 100.0

def test_cluster_analyzer_parses_violations(tmp_path):
    """違反を含むログからクラスタと集計が正しく抽出されることを検証"""
    log_file = tmp_path / "audit.jsonl"
    records = [
        {
            "trace_id": "t1",
            "sentinel_verdict": {
                "status": "BLOCK",
                "score": 0.0,
                "violations": [{"rule_id": "RULE-SEC-001", "severity": "CRITICAL", "message": "dangerous command"}]
            },
            "action_payload": {"tool_calls": [{"tool_name": "run_command", "status": "BLOCKED"}]}
        },
        {
            "trace_id": "t2",
            "sentinel_verdict": {
                "status": "PASS",
                "score": 100.0,
                "violations": []
            },
            "action_payload": {"tool_calls": [{"tool_name": "view_file", "status": "SUCCESS"}]}
        },
        {
            "trace_id": "t3",
            "sentinel_verdict": {
                "status": "BLOCK",
                "score": 0.0,
                "violations": [{"rule_id": "RULE-SKILL-001", "severity": "HIGH", "message": "unallowed tool"}]
            },
            "action_payload": {"tool_calls": [{"tool_name": "custom_eval_tool", "status": "BLOCKED"}]}
        },
    ]
    with open(log_file, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    analyzer = ClusterAnalyzer(log_path=log_file)
    summary = analyzer.analyze()

    assert summary.total_events == 3
    assert summary.pass_count == 1
    assert summary.block_count == 2
    assert summary.violation_clusters["RULE-SEC-001"] == 1
    assert summary.violation_clusters["RULE-SKILL-001"] == 1
    assert summary.blocked_tools["custom_eval_tool"] == 1

def test_patch_proposer_generates_recommendations():
    """多発するブロックツールに対してホワイトリスト追加パッチが提案されることを検証"""
    summary = AuditClusterSummary(
        total_events=10,
        pass_count=7,
        warn_count=0,
        block_count=3,
        blocked_tools={"docker_exec": 4},
        violation_clusters={"RULE-SKILL-001": 4, "RULE-DRIFT-001": 6}
    )
    proposer = PatchProposer(summary)
    recs = proposer.generate_recommendations()

    assert len(recs) == 2
    titles = [r["title"] for r in recs]
    assert any("docker_exec" in t for t in titles)
    assert any("drift_threshold" in t for t in titles)

    pr = proposer.generate_pr_proposal()
    assert pr is not None
    assert pr["branch"] == "refine/policy-tuning-batch"
    assert "docker_exec" in pr["body"]
