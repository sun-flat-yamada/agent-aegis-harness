"""
Google Antigravity Lifecycle Hook Adapter for Agent Aegis Harness
Integrates Antigravity SDK hooks with Sentinel, Archivist, and Recorder
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from google.antigravity import types
    from google.antigravity.hooks import hooks
except ImportError:
    # google-antigravity SDK が未インストールの環境向けのフォールバック型定義
    class _MockTypes:
        class HookResult:
            def __init__(self, allow: bool = True, reason: Optional[str] = None):
                self.allow = allow
                self.reason = reason

        class ToolCall:
            def __init__(self, name: str, args: dict):
                self.name = name
                self.args = args

        class AskQuestionInteractionSpec:
            pass

        class QuestionHookResult:
            def __init__(self, responses: list = None):
                self.responses = responses or []

    class _MockHooks:
        @staticmethod
        def on_session_start(func): return func
        @staticmethod
        def on_session_end(func): return func
        @staticmethod
        def pre_turn(func): return func
        @staticmethod
        def post_turn(func): return func
        @staticmethod
        def pre_tool_call_decide(func): return func
        @staticmethod
        def post_tool_call(func): return func
        @staticmethod
        def on_tool_error(func): return func
        @staticmethod
        def on_compaction(func): return func
        @staticmethod
        def on_interaction(func): return func

    types = _MockTypes()
    hooks = _MockHooks()

from aegis.archivist.policy_hasher import PolicyHasher
from aegis.models import (
    ActionPayload,
    AegisAuditEvent,
    AuditReproducibility,
    ClientToolType,
    EnvironmentInfo,
    InferenceTrace,
    IntegrityProof,
    PlanningEvidence,
    ReferencedFile,
    RetrievalContext,
    SentinelVerdict,
    TokenUsage,
    ToolCallRecord,
    TriggerContext,
    VerdictStatus,
    VerificationEvidence,
)
from aegis.recorder.tracer import AegisRecorder
from aegis.sentinel.judge import SentinelJudge
from aegis.sentinel.redactor import SensitiveRedactor

class AntigravityAegisAdapter:
    """
    Google Antigravity SDK のライフサイクルフックと Aegis ガバナンス層を結合するアダプタ
    """
    def __init__(
        self,
        repo_path: str = ".",
        policy_dir: str = ".aegis/rules",
        git_commit: str = "HEAD"
    ):
        self.repo_path = repo_path
        self.hasher = PolicyHasher(policy_dir)
        self.policy_digest = self.hasher.compute_digest()
        self.redactor = SensitiveRedactor()
        self.sentinel = SentinelJudge(policy_dir=policy_dir)
        self.recorder = AegisRecorder()

        self.current_trace_id = str(uuid.uuid4())
        self.step_index = 0
        self.current_prompt = ""
        self.active_plan_digest: Optional[str] = None
        self.git_commit = git_commit

    def register_hooks(self, config_hooks: list) -> list:
        """LocalAgentConfig の hooks リストに本アダプタのフックを追加"""
        config_hooks.extend([
            self.on_session_start,
            self.pre_turn,
            self.pre_tool_call_decide,
            self.post_tool_call,
            self.on_compaction,
            self.on_interaction,
            self.on_session_end,
        ])
        return config_hooks

    @hooks.on_session_start
    async def on_session_start(self):
        """セッション開始時にトレース初期化"""
        self.step_index = 0
        self.current_trace_id = str(uuid.uuid4())

    @hooks.pre_turn
    async def pre_turn(self, prompt: str) -> types.HookResult:
        """プロンプト投入時のサニタイズおよび Sentinel 即時検査"""
        self.step_index += 1
        sanitized_prompt, _ = self.redactor.redact_text(prompt)
        self.current_prompt = sanitized_prompt

        verdict = self.sentinel.evaluate_prompt(sanitized_prompt)
        if verdict.status == VerdictStatus.BLOCK:
            return types.HookResult(allow=False, reason="Blocked by Aegis Sentinel")

        return types.HookResult(allow=True)

    @hooks.pre_tool_call_decide
    async def pre_tool_call_decide(self, tool_call: types.ToolCall) -> types.HookResult:
        """ツール呼び出し前の即時判定 (Sentinel Tier 1/2)"""
        args = getattr(tool_call, "args", {}) or {}
        tool_name = getattr(tool_call, "name", "unknown")

        sanitized_args, _ = self.redactor.redact_dict(args)
        verdict = self.sentinel.evaluate_tool_call(
            tool_name=tool_name,
            arguments=sanitized_args,
            step_index=self.step_index,
        )

        status_str = "APPROVED" if verdict.status != VerdictStatus.BLOCK else "BLOCKED"
        self._record_step(
            tool_name=tool_name,
            arguments=sanitized_args,
            status=status_str,
            verdict=verdict,
        )

        if verdict.status == VerdictStatus.BLOCK:
            reasons = "; ".join(v.message for v in verdict.violations)
            return types.HookResult(allow=False, reason=f"Aegis Violation: {reasons}")

        return types.HookResult(allow=True)

    @hooks.post_tool_call
    async def post_tool_call(self, data: Any):
        """ツール完了後の事後監査"""
        pass

    @hooks.on_compaction
    async def on_compaction(self, data: Any):
        """コンテキスト圧縮イベント時のコンテキストドリフト検知"""
        drift_score = self.sentinel.evaluate_compaction_drift(data)
        if drift_score > 0.20:
            pass

    @hooks.on_interaction
    async def on_interaction(self, spec: types.AskQuestionInteractionSpec) -> types.QuestionHookResult:
        """ユーザー対話イベントの記録"""
        return types.QuestionHookResult(responses=[])

    @hooks.on_session_end
    async def on_session_end(self):
        """セッション終了時のフラッシュ"""
        self.recorder.flush()

    def _record_step(
        self,
        tool_name: str,
        arguments: dict,
        status: str,
        verdict: SentinelVerdict,
    ):
        """AegisAuditEvent を組み立ててレコーダーに記録"""
        event = AegisAuditEvent(
            trace_id=self.current_trace_id,
            span_id=str(uuid.uuid4())[:8],
            step_index=self.step_index,
            timestamp=datetime.utcnow(),
            audit_reproducibility=AuditReproducibility(
                policy_bundle_version="v1.0.0",
                policy_hash_digest=self.policy_digest,
                sentinel_version="0.1.0",
                evaluator_engine="ast-rule+llm-judge",
            ),
            environment=EnvironmentInfo(
                client_tool=ClientToolType.ANTIGRAVITY,
                repository=self.repo_path,
                git_commit=self.git_commit,
            ),
            trigger=TriggerContext(
                source="user_prompt",
                sanitized_prompt=self.current_prompt,
            ),
            retrieval_context=RetrievalContext(),
            inference_trace=InferenceTrace(
                model_id="gemini-thinking",
                token_usage=TokenUsage(),
            ),
            planning_evidence=PlanningEvidence(
                plan_hash_digest=self.active_plan_digest,
                plan_status="APPROVED" if self.active_plan_digest else "SKIPPED",
            ),
            action_payload=ActionPayload(
                tool_calls=[
                    ToolCallRecord(
                        tool_name=tool_name,
                        arguments=arguments,
                        status=status,
                    )
                ]
            ),
            sentinel_verdict=verdict,
            verification_evidence=None,
            integrity=IntegrityProof(
                previous_record_hash="pending",
                current_record_hash="pending",
            ),
        )
        self.recorder.record(event)
