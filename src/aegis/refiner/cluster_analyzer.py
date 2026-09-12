"""
Cluster Analyzer for Aegis Refiner
Analyzes historical audit logs to identify recurring friction, violations, and drift patterns
"""
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

@dataclass
class AuditClusterSummary:
    total_events: int = 0
    pass_count: int = 0
    warn_count: int = 0
    block_count: int = 0
    avg_score: float = 100.0
    violation_clusters: Dict[str, int] = field(default_factory=dict)
    blocked_tools: Dict[str, int] = field(default_factory=dict)
    sample_violations: List[Dict[str, Any]] = field(default_factory=list)

class ClusterAnalyzer:
    """
    Scans audit trail logs and clusters friction patterns
    """
    def __init__(self, log_path: Union[str, Path] = ".aegis/logs/audit-trail.jsonl"):
        self.log_path = Path(log_path)

    def analyze(self) -> AuditClusterSummary:
        """ログファイルを走査し、違反傾向とクラスタを集計"""
        summary = AuditClusterSummary()
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            return summary

        scores: List[float] = []
        rule_counter: Counter = Counter()
        tool_counter: Counter = Counter()
        samples: List[Dict[str, Any]] = []

        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    summary.total_events += 1

                    verdict = record.get("sentinel_verdict", {})
                    status = verdict.get("status", "PASS")
                    score = float(verdict.get("score", 100.0))
                    scores.append(score)

                    if status == "PASS":
                        summary.pass_count += 1
                    elif status == "WARN":
                        summary.warn_count += 1
                    elif status == "BLOCK":
                        summary.block_count += 1

                    violations = verdict.get("violations", [])
                    for v in violations:
                        rid = v.get("rule_id", "UNKNOWN")
                        rule_counter[rid] += 1
                        if len(samples) < 10:
                            samples.append({
                                "rule_id": rid,
                                "severity": v.get("severity", "MEDIUM"),
                                "message": v.get("message", ""),
                                "trace_id": record.get("trace_id", "")
                            })

                    # tool calls
                    tools = record.get("action_payload", {}).get("tool_calls", [])
                    for tc in tools:
                        if tc.get("status") == "BLOCKED":
                            tool_counter[tc.get("tool_name", "unknown")] += 1
                except Exception:
                    continue

        summary.avg_score = round(sum(scores) / len(scores), 2) if scores else 100.0
        summary.violation_clusters = dict(rule_counter.most_common())
        summary.blocked_tools = dict(tool_counter.most_common())
        summary.sample_violations = samples
        return summary
