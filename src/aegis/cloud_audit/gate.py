"""
Cloud Sentinel Gate Orchestrator for CI/CD Pipelines
Evaluates cloud runs, scans PR diffs, attests OIDC, and integrates with GitHub Actions.
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from aegis.archivist.policy_hasher import PolicyHasher
from aegis.cloud_audit.detector import CloudContextDetector
from aegis.cloud_audit.oidc import OIDCAttestationAdapter
from aegis.cloud_audit.scanner import CloudDiffScanner, DiffScanResult
from aegis.models import (
    ActionPayload,
    AegisAuditEvent,
    AuditReproducibility,
    ClientToolType,
    CloudWorkflowContext,
    EnvironmentInfo,
    InferenceTrace,
    IntegrityProof,
    OIDCAttestationClaim,
    RetrievalContext,
    SentinelVerdict,
    ToolCallRecord,
    TriggerContext,
    VerdictStatus,
    ViolationRecord,
    ViolationSeverity,
)
from aegis.recorder.tracer import AegisRecorder

class CloudSentinelVerdict(BaseModel):
    """クラウド CI 監査ゲートの総合判定モデル"""
    status: VerdictStatus
    score: float = Field(..., ge=0.0, le=100.0)
    violations: List[ViolationRecord] = Field(default_factory=list)
    cloud_context: Optional[CloudWorkflowContext] = None
    oidc_claim: Optional[OIDCAttestationClaim] = None
    diff_result: Optional[DiffScanResult] = None
    policy_digest: str = ""
    trace_id: Optional[str] = None

class CloudSentinelGate:
    """CI 環境下で Sentinel 即時監査・OIDC 真正性証明・PR 差分評価を統括するゲート"""

    def __init__(
        self,
        repo_path: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
    ):
        self.repo_path = repo_path or Path.cwd()
        self.env = env if env is not None else dict(os.environ)
        self.detector = CloudContextDetector(env=self.env)
        self.oidc_adapter = OIDCAttestationAdapter(env=self.env)
        self.scanner = CloudDiffScanner(repo_path=self.repo_path)
        self.hasher = PolicyHasher([str(self.repo_path / ".aegis/rules"), str(self.repo_path / ".skills")])

    def evaluate_ci_run(
        self,
        strict: bool = False,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
    ) -> CloudSentinelVerdict:
        """CI 実行の統合監査判定を実施"""
        # 1. コンテキスト検出
        context = self.detector.detect()
        if context and not base_ref and context.base_sha:
            base_ref = context.base_sha

        # 2. OIDC 真正性証明 (利用可能な場合)
        oidc_claim = self.oidc_adapter.fetch_and_attest()
        if oidc_claim and context:
            context.oidc_token_issuer = oidc_claim.iss
            context.job_workflow_ref = f"{oidc_claim.repository}/{oidc_claim.workflow}@{oidc_claim.ref}"

        # 3. PR 差分スキャン
        diff_result = self.scanner.scan_pr_diff(base_ref=base_ref, head_ref=head_ref)

        # 4. ポリシーハッシュ算出
        policy_digest = self.hasher.compute_digest()

        # 5. 違反集計と合否判定
        violations: List[ViolationRecord] = list(diff_result.violations)
        has_block = any(v.severity in (ViolationSeverity.CRITICAL, ViolationSeverity.HIGH) for v in violations)
        has_warn = any(v.severity in (ViolationSeverity.MEDIUM, ViolationSeverity.LOW) for v in violations)

        if has_block:
            verdict_status = VerdictStatus.BLOCK
            score = max(0.0, 100.0 - (len(violations) * 30.0))
        elif has_warn:
            verdict_status = VerdictStatus.WARN
            score = max(50.0, 100.0 - (len(violations) * 15.0))
        else:
            verdict_status = VerdictStatus.PASS
            score = 100.0

        trace_id = str(uuid.uuid4())

        # 6. 5W1H 監査イベントの記録 (ローカル WAL / OTel)
        self._record_audit_event(
            trace_id=trace_id,
            context=context,
            policy_digest=policy_digest,
            verdict_status=verdict_status,
            score=score,
            violations=violations,
            diff_result=diff_result,
        )

        # 7. GitHub Actions 出力への書き出し ($GITHUB_OUTPUT)
        self.export_github_step_outputs(
            verdict_status=verdict_status,
            policy_digest=policy_digest,
            violations_count=len(violations),
            files_inspected=len(diff_result.files_scanned),
        )

        return CloudSentinelVerdict(
            status=verdict_status,
            score=score,
            violations=violations,
            cloud_context=context,
            oidc_claim=oidc_claim,
            diff_result=diff_result,
            policy_digest=policy_digest,
            trace_id=trace_id,
        )

    def _record_audit_event(
        self,
        trace_id: str,
        context: Optional[CloudWorkflowContext],
        policy_digest: str,
        verdict_status: VerdictStatus,
        score: float,
        violations: List[ViolationRecord],
        diff_result: DiffScanResult,
    ) -> None:
        try:
            recorder = AegisRecorder(
                audit_trail_path=self.repo_path / ".aegis/logs/audit-trail.jsonl",
                forensic_trail_path=self.repo_path / ".aegis/logs/forensic-trail.jsonl",
            )
            env_info = EnvironmentInfo(
                client_tool=ClientToolType.CLI,
                repository=str(self.repo_path),
                git_commit=context.head_sha if context else "HEAD",
                cloud_workflow=context,
            )

            event = AegisAuditEvent(
                trace_id=trace_id,
                span_id=str(uuid.uuid4())[:8],
                step_index=1,
                timestamp=datetime.utcnow(),
                audit_reproducibility=AuditReproducibility(
                    policy_bundle_version="v1.0.0",
                    policy_hash_digest=policy_digest,
                    sentinel_version="0.1.0",
                    evaluator_engine="sentinel-cloud-gate",
                ),
                environment=env_info,
                trigger=TriggerContext(
                    source="ci_event",
                    sanitized_prompt=f"CI Gate Check for {context.event_name if context else 'manual'}",
                    redaction_applied=diff_result.masked_findings,
                ),
                retrieval_context=RetrievalContext(),
                inference_trace=InferenceTrace(),
                action_payload=ActionPayload(
                    tool_calls=[
                        ToolCallRecord(
                            tool_name="cloud_diff_scanner",
                            arguments={"files": diff_result.files_scanned},
                            status="SUCCESS",
                        )
                    ],
                    files_modified=diff_result.files_scanned,
                    file_diff_stat=diff_result.diff_stat,
                ),
                sentinel_verdict=SentinelVerdict(
                    status=verdict_status,
                    score=score,
                    tier_level="Tier 1 AST + Regex",
                    violations=violations,
                ),
                integrity=IntegrityProof(
                    previous_record_hash="pending",
                    current_record_hash="pending",
                ),
            )
            recorder.record(event)
        except Exception:
            # 記録エラーで CI ゲート自体をクラッシュさせない
            pass

    def export_github_step_outputs(
        self,
        verdict_status: VerdictStatus,
        policy_digest: str,
        violations_count: int,
        files_inspected: int,
    ) -> None:
        """GitHub Actions の $GITHUB_OUTPUT ファイルに出力キー・バリューを追記"""
        output_path = self.env.get("GITHUB_OUTPUT")
        if not output_path:
            return

        try:
            p = Path(output_path)
            lines = [
                f"verdict={verdict_status.value}\n",
                f"policy_digest={policy_digest}\n",
                f"violations_count={violations_count}\n",
                f"files_inspected={files_inspected}\n",
            ]
            with p.open("a", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception:
            pass
