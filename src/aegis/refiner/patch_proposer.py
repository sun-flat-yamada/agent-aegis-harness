"""
Patch Proposer for Aegis Refiner
Generates policy/skill update recommendations and Git PR proposals based on clustered audit findings
"""
from typing import Dict, List, Optional
from aegis.refiner.cluster_analyzer import AuditClusterSummary

class PatchProposer:
    """
    Generates rule and skill optimization patches
    """
    def __init__(self, summary: AuditClusterSummary):
        self.summary = summary

    def generate_recommendations(self) -> List[Dict[str, str]]:
        """分析サマリーを元に推奨パッチ一覧を生成"""
        recommendations: List[Dict[str, str]] = []

        # 1. 頻出ブロックツールのホワイトリスト緩和提案
        for tool, count in self.summary.blocked_tools.items():
            if count >= 3:
                recommendations.append({
                    "target_file": ".aegis/rules/skill-compliance-policy.yaml",
                    "action": "ADD_ALLOWED_TOOL",
                    "title": f"Add '{tool}' to allowed_tools_whitelist",
                    "description": f"Tool '{tool}' was blocked {count} times. Review if this tool is legitimate for the development workflow.",
                    "patch": f"allowed_tools_whitelist:\n  - \"{tool}\""
                })

        # 2. ドリフト警告頻出時の閾値調整
        drift_count = self.summary.violation_clusters.get("RULE-DRIFT-001", 0)
        if drift_count >= 5:
            recommendations.append({
                "target_file": ".aegis/rules/context-drift-policy.yaml",
                "action": "ADJUST_DRIFT_THRESHOLD",
                "title": "Evaluate relaxing drift_threshold or improving prompt context retention",
                "description": f"Context drift policy triggered {drift_count} times. Consider tuning threshold from 0.20 to 0.25.",
                "patch": "drift_threshold: 0.25"
            })

        return recommendations

    def generate_pr_proposal(self) -> Optional[Dict[str, str]]:
        """Git Pull Request 提案メタデータを生成"""
        recs = self.generate_recommendations()
        if not recs:
            return None

        branch_name = "refine/policy-tuning-batch"
        title = "refactor(rules): optimize Aegis audit policies based on historical log cluster"
        body_lines = [
            "## Automated Policy Refinement Proposal",
            "",
            f"Analyzed **{self.summary.total_events}** audit events across local sessions.",
            f"- Pass rate: {round((self.summary.pass_count / self.summary.total_events) * 100, 1) if self.summary.total_events else 100}%",
            f"- Blocks: {self.summary.block_count}",
            f"- Warnings: {self.summary.warn_count}",
            "",
            "### Proposed Adjustments:"
        ]
        for rec in recs:
            body_lines.append(f"- **{rec['title']}** (`{rec['target_file']}`)")
            body_lines.append(f"  > {rec['description']}")

        return {
            "branch": branch_name,
            "title": title,
            "body": "\n".join(body_lines),
            "recommendations": recs,
        }
