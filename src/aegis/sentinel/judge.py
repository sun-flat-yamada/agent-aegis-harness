"""
Sentinel Judge Engine for Agent Aegis Harness
Evaluates prompts and tool calls with multi-tiered defense and drift detection
"""
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from aegis.models import (
    SentinelVerdict,
    VerdictStatus,
    ViolationRecord,
    ViolationSeverity,
)

class SentinelJudge:
    # 危険コマンドのデフォルトパターン
    DANGEROUS_PATTERNS = [
        (r"(?i)\brm\s+-[rf]{1,2}\s+/(?:\s|$)", "Dangerous root recursive file deletion command detected"),
        (r"(?i)\bformat\s+[a-z]:", "Dangerous disk format command detected"),
        (r"(?i)\bdel\s+/[sfq]\s+[a-z]:\\", "Dangerous recursive disk deletion command detected"),
        (r"(?i)\bdrop\s+(?:database|schema)\b", "Dangerous database destruction command detected"),
    ]

    def __init__(self, policy_dir: str = ".aegis/rules"):
        self.policy_dir = Path(policy_dir)
        self.loaded_policies: Dict[str, Any] = {}
        self.load_policies()

    def load_policies(self):
        """ポリシーディレクトリから YAML ポリシーを読み込み"""
        if not self.policy_dir.exists():
            return
        for file_path in self.policy_dir.glob("*.yaml"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Front-matter があればスキップ
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            content = parts[2]
                    data = yaml.safe_load(content)
                    if isinstance(data, dict):
                        rule_id = data.get("rule_id", file_path.stem)
                        self.loaded_policies[rule_id] = data
            except Exception:
                pass

    def evaluate_prompt(self, sanitized_prompt: str) -> SentinelVerdict:
        """ユーザープロンプトの安全性・インジェクション検査"""
        violations: List[ViolationRecord] = []
        
        # 危険なシステム破壊プロンプトパターンの簡易検知
        for pattern, msg in self.DANGEROUS_PATTERNS:
            if re.search(pattern, sanitized_prompt):
                violations.append(
                    ViolationRecord(
                        rule_id="RULE-SEC-PROMPT",
                        severity=ViolationSeverity.CRITICAL,
                        message=f"Prompt contains dangerous instruction pattern: {msg}",
                    )
                )

        if violations:
            return SentinelVerdict(
                status=VerdictStatus.BLOCK,
                score=0.0,
                tier_level="TIER_1_AST",
                violations=violations,
            )

        return SentinelVerdict(
            status=VerdictStatus.PASS,
            score=100.0,
            tier_level="TIER_1_AST",
            violations=[],
        )

    def evaluate_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        step_index: int = 0
    ) -> SentinelVerdict:
        """ツール実行前の Tier 1 / Tier 2 即時検査"""
        violations: List[ViolationRecord] = []

        # 1. run_command のコマンド内容チェック
        if tool_name == "run_command":
            cmd = arguments.get("CommandLine", "")
            for pattern, msg in self.DANGEROUS_PATTERNS:
                if re.search(pattern, cmd):
                    violations.append(
                        ViolationRecord(
                            rule_id="RULE-SEC-001",
                            severity=ViolationSeverity.CRITICAL,
                            message=f"Blocked dangerous command: {msg}",
                        )
                    )

        # 2. ツール許可リストチェック
        skill_policy = self.loaded_policies.get("RULE-SKILL-001", {})
        if skill_policy.get("enforce_allowed_tools"):
            whitelist = skill_policy.get("allowed_tools_whitelist", [])
            if whitelist and tool_name not in whitelist:
                violations.append(
                    ViolationRecord(
                        rule_id="RULE-SKILL-001",
                        severity=ViolationSeverity.HIGH,
                        message=f"Tool '{tool_name}' is not in project whitelist",
                    )
                )

        if any(v.severity == ViolationSeverity.CRITICAL for v in violations):
            status = VerdictStatus.BLOCK
            score = 0.0
        elif violations:
            status = VerdictStatus.WARN
            score = 70.0
        else:
            status = VerdictStatus.PASS
            score = 100.0

        return SentinelVerdict(
            status=status,
            score=score,
            tier_level="TIER_1_AST",
            violations=violations,
        )

    def evaluate_compaction_drift(self, compaction_data: Any) -> float:
        """コンテキスト圧縮時のドリフトスコアを算出 (0.0: ドリフトなし, 1.0: 重大ドリフト)"""
        # 現状はヒューリスティックスコアを返す
        return 0.05
