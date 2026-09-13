"""
Core Data Models for Agent Aegis Harness
Draft-07 Schema Compliant with Google Antigravity Extensions
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ClientToolType(str, Enum):
    ANTIGRAVITY = "google-antigravity"
    CLAUDE_CODE = "claude-code"
    COPILOT = "github-copilot"
    GITHUB_COPILOT = "github-copilot"
    GITHUB_COPILOT_CLI = "github-copilot-cli"
    AWS_KIRO = "aws-kiro"
    CURSOR = "cursor"
    WINDSURF = "windsurf"
    CLI = "cli"

class VerdictStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"

class ViolationSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class AuditReproducibility(BaseModel):
    policy_bundle_version: str = Field(..., description="ポリシーバンドルバージョン")
    policy_hash_digest: str = Field(..., description="ルール・スキルの sha256 決定論的ダイジェスト")
    sentinel_version: str = Field(..., description="Sentinel バージョン")
    evaluator_engine: str = Field(..., description="評価エンジン識別子")

class CloudPlatformType(str, Enum):
    GITHUB_ACTIONS = "github-actions"
    AZURE_PIPELINES = "azure-pipelines"
    AWS_CODEBUILD = "aws-codebuild"
    GENERIC_CI = "generic-ci"

class ActorType(str, Enum):
    HUMAN = "human"
    BOT = "bot"
    AUTONOMOUS_CLOUD_AGENT = "autonomous-cloud-agent"

class CloudWorkflowContext(BaseModel):
    """クラウド CI/CD ランナーおよびリモートエージェント実行環境の 5W1H メタデータ"""
    platform: CloudPlatformType = Field(default=CloudPlatformType.GITHUB_ACTIONS, description="CI/CD プラットフォーム識別子")
    workflow_name: str = Field(..., description="GitHub Actions ワークフロー名 (.github/workflows/...)")
    workflow_run_id: str = Field(..., description="GITHUB_RUN_ID (一意のジョブ実行 ID)")
    workflow_run_attempt: int = Field(default=1, description="GITHUB_RUN_ATTEMPT (再試行回数)")
    job_id: str = Field(..., description="GITHUB_JOB (実行ジョブ名)")
    runner_environment: str = Field(default="github-hosted", description="github-hosted または self-hosted")
    event_name: str = Field(..., description="発火イベント名 (pull_request, push, etc.)")
    actor: str = Field(..., description="実行トリガー者 (例: github-actions[bot], copilot-agent)")
    actor_type: ActorType = Field(default=ActorType.HUMAN, description="human, bot, または autonomous-cloud-agent")
    pr_number: Optional[int] = Field(None, description="対象プルリクエスト番号")
    head_sha: str = Field(..., description="コミット HEAD SHA")
    base_sha: Optional[str] = Field(None, description="比較ベースコミット SHA (PR時)")
    oidc_token_issuer: Optional[str] = Field(None, description="OIDC トークン発行者")
    job_workflow_ref: Optional[str] = Field(None, description="OIDC クレーム: 実行されたワークフロー定義の不変参照")

class OIDCAttestationClaim(BaseModel):
    """GitHub OIDC ID Token の検証済みクレームモデル"""
    iss: str = Field(..., description="Issuer URL")
    sub: str = Field(..., description="Subject claim")
    aud: str = Field(..., description="Audience")
    repository: str = Field(..., description="対象リポジトリ")
    repository_owner: Optional[str] = Field(None, description="リポジトリオーナー")
    ref: Optional[str] = Field(None, description="Git Ref")
    sha: Optional[str] = Field(None, description="コミット SHA")
    workflow: Optional[str] = Field(None, description="ワークフローパス")
    run_id: Optional[str] = Field(None, description="Run ID")
    raw_token_sha256: str = Field(..., description="JWT トークンの SHA-256 ダイジェスト")

class EnvironmentInfo(BaseModel):
    client_tool: ClientToolType
    client_version: Optional[str] = None
    repository: str
    git_commit: str
    user_hash: Optional[str] = None
    session_id: Optional[str] = None
    subagent_depth: int = 0
    parent_trace_id: Optional[str] = None
    cloud_workflow: Optional[CloudWorkflowContext] = None

class TriggerContext(BaseModel):
    source: str
    sanitized_prompt: str
    redaction_applied: List[str] = Field(default_factory=list)

class ReferencedFile(BaseModel):
    path: str
    blob_sha: str
    token_count: Optional[int] = None

class RetrievalContext(BaseModel):
    referenced_files: List[ReferencedFile] = Field(default_factory=list)
    loaded_skills: List[str] = Field(default_factory=list)
    loaded_rules: List[str] = Field(default_factory=list)
    knowledge_items: List[str] = Field(default_factory=list)

class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    candidates_tokens: int = 0
    thoughts_tokens: int = 0  # Antigravity Extended Thinking
    cached_tokens: int = 0
    total_tokens: int = 0

class InferenceTrace(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_id: Optional[str] = None
    reasoning_summary: Optional[str] = None
    token_usage: TokenUsage = Field(default_factory=TokenUsage)

class PlanningEvidence(BaseModel):
    plan_artifact_path: Optional[str] = None
    plan_hash_digest: Optional[str] = None
    plan_status: Optional[str] = None

class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    status: str
    error_message: Optional[str] = None

class ActionPayload(BaseModel):
    tool_calls: List[ToolCallRecord] = Field(default_factory=list)
    file_diff_stat: Optional[str] = None
    files_modified: List[str] = Field(default_factory=list)

class ViolationRecord(BaseModel):
    rule_id: str
    severity: ViolationSeverity
    message: str

class SentinelVerdict(BaseModel):
    status: VerdictStatus
    score: float = Field(..., ge=0.0, le=100.0)
    tier_level: str
    violations: List[ViolationRecord] = Field(default_factory=list)

class VerificationEvidence(BaseModel):
    walkthrough_path: Optional[str] = None
    walkthrough_digest: Optional[str] = None
    tests_passed: Optional[bool] = None
    evidence_media: List[str] = Field(default_factory=list)

class IntegrityProof(BaseModel):
    previous_record_hash: str
    current_record_hash: str

class AegisAuditEvent(BaseModel):
    trace_id: str
    span_id: str
    step_index: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    audit_reproducibility: AuditReproducibility
    environment: EnvironmentInfo
    trigger: TriggerContext
    retrieval_context: RetrievalContext = Field(default_factory=RetrievalContext)
    inference_trace: InferenceTrace = Field(default_factory=InferenceTrace)
    planning_evidence: Optional[PlanningEvidence] = None
    action_payload: ActionPayload = Field(default_factory=ActionPayload)
    sentinel_verdict: SentinelVerdict
    verification_evidence: Optional[VerificationEvidence] = None
    integrity: IntegrityProof

class StorageMode(str, Enum):
    AZURE_FULL = "azure-full"
    GITHUB_LITE = "github-lite"

class AzureFullConfig(BaseModel):
    event_hubs_connection_str: Optional[str] = Field(None, description="Event Hubs connection string (Env recommended)")
    event_hubs_name: str = Field("aegis-audit-events", description="Event Hub entity name")
    blob_account_name: str = Field(..., description="Azure Blob Storage Account name")
    blob_container: str = Field("aegis-audit-worm", description="Immutable WORM Container name")
    log_analytics_workspace_id: Optional[str] = Field(None, description="Log Analytics Workspace ID")
    otlp_endpoint: str = Field("https://aegis-ingress.corp.internal:4317", description="Ingress Gateway OTLP Endpoint")

class GitHubLiteConfig(BaseModel):
    audit_repository: str = Field(..., description="Audit logs dedicated repository (e.g. org/aegis-audit-logs)")
    branch: str = Field("main", description="Anchor branch name")
    auth_method: str = Field("oidc", description="Authentication method (oidc | deploy_key | pat)")
    deploy_key_secret_env: str = Field("AEGIS_AUDIT_DEPLOY_KEY", description="Deploy key env var name")
    upload_target: str = Field("releases", description="Upload target (releases | branch_commit)")
    compression: str = Field("zstd", description="Compression algorithm (zstd | gzip)")
    batch_interval_minutes: int = Field(60, description="Local aggregation batch interval")
    retention_years: int = Field(3, ge=3, le=10, description="Retention duration in years")

class AuditStorageConfig(BaseModel):
    mode: StorageMode = Field(StorageMode.AZURE_FULL, description="Audit storage mode")
    azure_full: Optional[AzureFullConfig] = None
    github_lite: Optional[GitHubLiteConfig] = None

class MerkleProof(BaseModel):
    batch_id: str
    batch_timestamp: datetime
    leaf_index: int
    total_leaves: int
    merkle_root: str
    audit_path: List[str] = Field(..., description="Sibling hash path (Log2 N)")
    anchor_commit_sha: Optional[str] = None

class GovernanceKPIItem(BaseModel):
    kpi_id: str
    name: str
    current_value: float
    previous_value: float
    delta_percent: float
    status: str = Field(..., description="NORMAL | WARNING | CRITICAL")
    target_threshold: float
    reference_standard: str = Field(..., description="Standard reference (e.g. ISO/IEC 42001, NIST AI RMF)")
    reference_url: str = Field(..., description="Standard reference URL")
    guidance: str = Field(..., description="Improvement intent & remediation guidance")

class WeeklyGovernanceReport(BaseModel):
    report_id: str
    period_start: datetime
    period_end: datetime
    generation_time: datetime = Field(default_factory=datetime.utcnow)
    overall_status: str = Field(..., description="NORMAL | WARNING | CRITICAL")
    executive_summary: str
    total_active_projects: int
    total_active_users: int
    total_tool_executions: int
    kpi_metrics: List[GovernanceKPIItem]
    incident_highlights: List[Dict[str, Any]] = Field(default_factory=list)
    project_compliance_ranking: List[Dict[str, Any]] = Field(default_factory=list)
    sign_off_status: Dict[str, Optional[str]] = Field(default_factory=dict)


class TriggerSourceType(str, Enum):
    CHAT_PROMPT = "chat_prompt"
    INLINE_EDIT = "inline_edit"
    TERMINAL_COMMAND = "terminal_command"
    MCP_TOOL_CALL = "mcp_tool_call"
    GIT_COMMIT = "git_commit"


class NormalizedTrigger(BaseModel):
    source: TriggerSourceType
    raw_prompt: Optional[str] = None
    sanitized_prompt: str
    user_identity: str
    session_id: str


class NormalizedInference(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_name: Optional[str] = None
    chain_of_thought_summary: Optional[str] = None
    raw_thinking_hash: Optional[str] = None
    user_intent_summary: Optional[str] = None


class NormalizedToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    output_summary: Optional[str] = None
    status: str = "SUCCESS"  # SUCCESS | ERROR | BLOCKED


class ForensicProvenance(BaseModel):
    """後追い抽出データのフォレンジクス完全性と探索諸元"""
    source_path: str = Field(..., description="抽出元のローカルファイル絶対パス")
    source_sha256: str = Field(..., description="抽出元ファイルの SHA-256 ダイジェスト")
    parser_id: str = Field(..., description="解析に使用したパーサー識別子 (例: copilot-delta-v1)")
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow, description="抽出実行日時")
    confidence_level: str = Field("HIGH", description="復元完全性の確信度 (HIGH | MEDIUM | LOW)")
    raw_record_kind: Optional[int] = Field(None, description="VS Code Delta Record Kind")


class GitCorrelationContext(BaseModel):
    commit_sha: Optional[str] = None
    commit_timestamp: Optional[datetime] = None
    commit_author: Optional[str] = None
    commit_message: Optional[str] = None
    branch_name: Optional[str] = None
    staged_files: List[str] = Field(default_factory=list)
    diff_hash: Optional[str] = None
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="コミット紐付け総合確信度 (0.0~1.0)")
    confidence_level: str = Field(default="UNLINKED", description="HIGH | MEDIUM | LOW | UNLINKED")
    correlation_proof: Optional[str] = None


class NormalizedAIEvent(BaseModel):
    """マルチツール共通の正規化 5W1H 監査イベント"""
    event_id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    trace_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    client_tool: ClientToolType

    # 諸元・プロベナンス拡張
    extraction_method: str = Field(default="realtime_hook", description="realtime_hook | retro_local_discovery")
    tags: List[str] = Field(default_factory=list, description="諸元識別タグ (例: source:github-copilot, extraction:retroactive)")
    forensic_provenance: Optional[ForensicProvenance] = Field(None, description="事後抽出フォレンジクス諸元")

    trigger: NormalizedTrigger
    inference: NormalizedInference = Field(default_factory=NormalizedInference)
    tool_calls: List[NormalizedToolCall] = Field(default_factory=list)
    affected_files: List[str] = Field(default_factory=list)
    git_context: Optional[GitCorrelationContext] = None

    sentinel_verdict_status: str = "ALLOW"  # ALLOW | WARN | BLOCK
    policy_hash_digest: str = "pending"
    previous_record_hash: str = "pending"
    current_record_hash: str = "pending"

