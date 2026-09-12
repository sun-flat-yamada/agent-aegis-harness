"""
CI / Cloud Environment Detection Module for Agent Aegis Harness
Detects GitHub Actions and remote agent execution contexts.
"""
import os
import re
from typing import Dict, Optional
from pathlib import Path

from aegis.models import (
    ActorType,
    CloudPlatformType,
    CloudWorkflowContext,
)

class CloudContextDetector:
    """自動的に CI/CD 環境変数から CloudWorkflowContext を抽出・分類するディテクタ"""

    def __init__(self, env: Optional[Dict[str, str]] = None):
        self.env = env if env is not None else dict(os.environ)

    def is_ci_environment(self) -> bool:
        """CI 環境下で稼働しているかを判定"""
        return (
            self.env.get("CI") == "true"
            or self.env.get("GITHUB_ACTIONS") == "true"
            or "ACTIONS_ID_TOKEN_REQUEST_URL" in self.env
        )

    def detect(self) -> Optional[CloudWorkflowContext]:
        """環境変数から CloudWorkflowContext を生成。非 CI 環境時は None を返却"""
        if self.env.get("GITHUB_ACTIONS") == "true" or "ACTIONS_ID_TOKEN_REQUEST_URL" in self.env:
            return self._detect_github_actions()
        elif self.env.get("CI") == "true":
            return self._detect_generic_ci()
        return None

    def _classify_actor(self, actor: str) -> ActorType:
        """アクター名から人間、ボット、または自律クラウドエージェントを判定"""
        actor_lower = actor.lower()
        if (
            "copilot" in actor_lower
            or "autonomous" in actor_lower
            or "coding-agent" in actor_lower
            or "workspace" in actor_lower
        ):
            return ActorType.AUTONOMOUS_CLOUD_AGENT
        elif (
            "[bot]" in actor_lower
            or actor_lower.endswith("-bot")
            or actor_lower == "github-actions"
            or "automation" in actor_lower
        ):
            return ActorType.BOT
        return ActorType.HUMAN

    def _extract_pr_number(self) -> Optional[int]:
        """GITHUB_REF または GITHUB_REF_NAME から PR 番号を抽出"""
        ref = self.env.get("GITHUB_REF", "")
        # e.g., refs/pull/42/merge
        match = re.search(r"refs/pull/(\d+)/", ref)
        if match:
            return int(match.group(1))

        ref_name = self.env.get("GITHUB_REF_NAME", "")
        # e.g., 42/merge
        match_name = re.match(r"^(\d+)/", ref_name)
        if match_name:
            return int(match_name.group(1))
        return None

    def _detect_github_actions(self) -> CloudWorkflowContext:
        """GitHub Actions 特有の環境変数をパース"""
        actor = self.env.get("GITHUB_ACTOR", "unknown-actor")
        actor_type = self._classify_actor(actor)
        pr_number = self._extract_pr_number()

        workflow_name = self.env.get("GITHUB_WORKFLOW", "unknown-workflow")
        workflow_run_id = self.env.get("GITHUB_RUN_ID", "local-run")
        try:
            workflow_run_attempt = int(self.env.get("GITHUB_RUN_ATTEMPT", "1"))
        except ValueError:
            workflow_run_attempt = 1

        job_id = self.env.get("GITHUB_JOB", "audit-gate")
        runner_environment = self.env.get("RUNNER_ENVIRONMENT", "github-hosted")
        event_name = self.env.get("GITHUB_EVENT_NAME", "workflow_dispatch")

        head_sha = self.env.get("GITHUB_SHA", "HEAD")
        base_sha = self.env.get("GITHUB_BASE_REF") or None

        # OIDC Issuer は GitHub Actions 標準
        oidc_issuer = None
        if "ACTIONS_ID_TOKEN_REQUEST_URL" in self.env:
            oidc_issuer = "https://token.actions.githubusercontent.com"

        job_workflow_ref = self.env.get("GITHUB_WORKFLOW_REF") or None

        return CloudWorkflowContext(
            platform=CloudPlatformType.GITHUB_ACTIONS,
            workflow_name=workflow_name,
            workflow_run_id=workflow_run_id,
            workflow_run_attempt=workflow_run_attempt,
            job_id=job_id,
            runner_environment=runner_environment,
            event_name=event_name,
            actor=actor,
            actor_type=actor_type,
            pr_number=pr_number,
            head_sha=head_sha,
            base_sha=base_sha,
            oidc_token_issuer=oidc_issuer,
            job_workflow_ref=job_workflow_ref,
        )

    def _detect_generic_ci(self) -> CloudWorkflowContext:
        """汎用 CI 環境のフォールバック検知"""
        return CloudWorkflowContext(
            platform=CloudPlatformType.GENERIC_CI,
            workflow_name=self.env.get("CI_PIPELINE_NAME", "generic-ci-job"),
            workflow_run_id=self.env.get("CI_JOB_ID", "1"),
            workflow_run_attempt=1,
            job_id=self.env.get("CI_JOB_NAME", "audit"),
            runner_environment="ci-runner",
            event_name="push",
            actor=self.env.get("USER", "ci-bot"),
            actor_type=ActorType.BOT,
            head_sha=self.env.get("GIT_COMMIT", "HEAD"),
        )
