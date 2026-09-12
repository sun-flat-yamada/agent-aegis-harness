---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "architecture_doc"
id: "SPEC-CLOUDFLOW-001"
title: "Agent Aegis Harness (aah) - クラウドワークフロー & リモートエージェント監査詳細仕様書 (Specification)"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: ".devs/changes/2026-09-12_AddSupportCloudFlowAudit/spec.md"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.4.0"
tags: ["specification", "cloud-audit", "ci-cd", "github-actions", "copilot-app", "remote-agent", "oidc", "worm"]
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
---

# Agent Aegis Harness (aah) - クラウドワークフロー & リモートエージェント監査詳細仕様書

**Document ID:** SPEC-CLOUDFLOW-001 | **Version:** 1.0.0 | **Status:** Active | **Author:** @sun-flat-yamada (Youhei Yamada)  
**Parent Blueprint:** [`blueprint.md`](./blueprint.md) | **Target Change:** `.devs/changes/2026-09-12_AddSupportCloudFlowAudit`  
**System Architecture:** [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)

---

## 1. システム全体像とドメインモデル

### 1.1 目的とスコープ
本仕様書は、`blueprint.md` にて定義された構想に基づき、GitHub Actions 等のクラウド CI/CD ランナーおよび GitHub Copilot Coding Agent 等のリモート自律エージェントに対する 5W1H 監査統制と改ざん防止機能の詳細仕様を規定します。

エフェメラル（使い捨て）ランナー環境下においても、暗号学的真正性（GitHub OIDC Token）、即時セマンティック検閲（Sentinel Cloud Gate）、および全社 WORM 不変ストレージへのログ転送（OTel Dual Streamer）を決定論的に実現します。

### 1.2 クラウド監査ドメインモデル

```mermaid
classDiagram
    class CloudWorkflowContext {
        +str platform
        +str workflow_name
        +str workflow_run_id
        +int workflow_run_attempt
        +str job_id
        +str runner_environment
        +str event_name
        +str actor
        +str actor_type
        +int pr_number
        +str head_sha
        +str base_sha
        +str oidc_token_issuer
        +str job_workflow_ref
    }

    class OIDCAttestationClaim {
        +str iss
        +str sub
        +str aud
        +str repository
        +str repository_owner
        +str ref
        +str sha
        +str workflow
        +str run_id
        +str runner_environment
        +bool is_valid
        +str raw_token_hash
    }

    class CloudSentinelVerdict {
        +str verdict_status
        +float score
        +List~ViolationRecord~ violations
        +List~str~ redactor_findings
        +int files_inspected
        +bool oidc_verified
        +str policy_digest
    }

    class EnvironmentInfo {
        +ClientToolType client_tool
        +str repository
        +str git_commit
        +CloudWorkflowContext cloud_workflow
    }

    EnvironmentInfo "1" *-- "0..1" CloudWorkflowContext : includes
    CloudWorkflowContext "1" o-- "0..1" OIDCAttestationClaim : verified_by
    CloudSentinelVerdict "1" ..> CloudWorkflowContext : evaluates
```

---

## 2. データ構造 & スキーマ定義

### 2.1 `CloudWorkflowContext` Pydantic v2 定義
`src/aegis/models.py` の `EnvironmentInfo` にオプション属性 `cloud_workflow: Optional[CloudWorkflowContext] = None` として統合されます。

```python
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

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
    platform: CloudPlatformType = Field(
        default=CloudPlatformType.GITHUB_ACTIONS,
        description="CI/CD プラットフォーム識別子"
    )
    workflow_name: str = Field(..., description="ワークフロー名 (.github/workflows/...)")
    workflow_run_id: str = Field(..., description="一意のジョブ実行 ID (例: GITHUB_RUN_ID)")
    workflow_run_attempt: int = Field(default=1, description="再試行回数 (GITHUB_RUN_ATTEMPT)")
    job_id: str = Field(..., description="実行ジョブ名 (GITHUB_JOB)")
    runner_environment: str = Field(
        default="github-hosted",
        description="ランナー種別 (github-hosted または self-hosted)"
    )
    
    # イベント & アクター
    event_name: str = Field(..., description="発火イベント名 (pull_request, push, schedule, etc.)")
    actor: str = Field(..., description="実行トリガー者 (例: github-actions[bot], copilot-agent)")
    actor_type: ActorType = Field(
        default=ActorType.HUMAN,
        description="実行主体カテゴリ (human | bot | autonomous-cloud-agent)"
    )
    pr_number: Optional[int] = Field(None, description="対象プルリクエスト番号")
    head_sha: str = Field(..., description="コミット HEAD SHA")
    base_sha: Optional[str] = Field(None, description="比較ベースコミット SHA (PR時)")
    
    # OIDC 真正性証明メタデータ
    oidc_token_issuer: Optional[str] = Field(
        None,
        description="OIDC トークン発行者 (例: https://token.actions.githubusercontent.com)"
    )
    job_workflow_ref: Optional[str] = Field(
        None,
        description="OIDC クレーム: 実行されたワークフロー定義の不変参照"
    )
```

### 2.2 `OIDCAttestationClaim` 定義
GitHub Actions OIDC JWT トークンのデコードおよび検証結果モデル：

```python
class OIDCAttestationClaim(BaseModel):
    """GitHub OIDC ID Token の検証済みクレームモデル"""
    iss: str = Field(..., description="Issuer URL")
    sub: str = Field(..., description="Subject claim (repo:org/name:ref:...)")
    aud: str = Field(..., description="Audience (通常 aegis-audit または sts.amazonaws.com 等)")
    repository: str = Field(..., description="対象リポジトリ (owner/repo)")
    repository_owner: str = Field(..., description="リポジトリオーナー")
    ref: str = Field(..., description="Git Ref (refs/pull/.../merge または refs/heads/...)")
    sha: str = Field(..., description="コミット SHA")
    workflow: str = Field(..., description="ワークフロー定義ファイルパス")
    run_id: str = Field(..., description="Run ID")
    raw_token_sha256: str = Field(..., description="JWT トークンの SHA-256 ダイジェスト (平文トークンは非保持)")
```

### 2.3 JSON Schema 拡張仕様 (`.aegis/schemas/audit-event.schema.json`)
`environment` オブジェクト配下に `cloud_workflow` プロパティを追加：

```json
"cloud_workflow": {
  "type": "object",
  "required": [
    "platform",
    "workflow_name",
    "workflow_run_id",
    "job_id",
    "event_name",
    "actor",
    "head_sha"
  ],
  "properties": {
    "platform": { "type": "string" },
    "workflow_name": { "type": "string" },
    "workflow_run_id": { "type": "string" },
    "workflow_run_attempt": { "type": "integer" },
    "job_id": { "type": "string" },
    "runner_environment": { "type": "string" },
    "event_name": { "type": "string" },
    "actor": { "type": "string" },
    "actor_type": { "type": "string", "enum": ["human", "bot", "autonomous-cloud-agent"] },
    "pr_number": { "type": "integer" },
    "head_sha": { "type": "string" },
    "base_sha": { "type": "string" },
    "oidc_token_issuer": { "type": "string" },
    "job_workflow_ref": { "type": "string" }
  }
}
```

---

## 3. インターフェース仕様

### 3.1 CLI インターフェース拡張 (`aah check --ci`)

`aah check` コマンドに `--ci` フラグを追加します。

```text
Usage: aah check [OPTIONS]

Options:
  --strict             Fail with non-zero exit on warnings
  --ci                 Execute in Cloud CI mode: auto-detect environment,
                       scan PR diffs, attest OIDC, and emit cloud audit
  --output-json PATH   Write detailed audit verdict JSON to file
  --help               Show this message and exit.
```

#### 実行時動作フロー:
1. **CI 環境自動検出**:
   - `GITHUB_ACTIONS == "true"` を検出し、GitHub Actions 特有の環境変数を自動パース。
   - アクター名に `[bot]` や `copilot` が含まれる場合、`actor_type` を `autonomous-cloud-agent` に自動分類。
2. **PR 差分自動スキャン**:
   - PR イベントの場合、`git diff origin/${GITHUB_BASE_REF}...HEAD` を自動取得。
   - 変更ファイル群に対し、Sensitive Redactor（秘密鍵・トークン・PII）および Sentinel ルールを適用。
3. **GitHub OIDC トークン Attestation**:
   - 環境変数 `ACTIONS_ID_TOKEN_REQUEST_URL` および `ACTIONS_ID_TOKEN_REQUEST_TOKEN` が存在する場合、Keyless OIDC トークンをリクエスト取得。
   - トークンの Payload を検証し、`job_workflow_ref` やリポジトリの一致を確認。
4. **CI ステップ出力 ($GITHUB_OUTPUT)**:
   - 環境変数 `GITHUB_OUTPUT` が指定されている場合、次のキー・バリューを出力：
     - `verdict=PASS | WARN | BLOCK`
     - `policy_digest=sha256:...`
     - `violations_count=N`
     - `cloud_context_json={...}`
5. **終了コード**:
   - `BLOCK` 検出時: 終了コード `1`（CI ジョブ失敗、マージ阻止）。
   - `WARN` 検出かつ `--strict` 有効時: 終了コード `1`。
   - 合格時: 終了コード `0`。

### 3.2 GitHub Actions Composite Action 仕様 (`.github/actions/aah-cloud-audit/action.yml`)

```yaml
name: "Agent Aegis Cloud Audit Gate"
description: "Instant Sentinel Audit, Secret Redactor, and OIDC Attestation for AI-driven PRs"
author: "@sun-flat-yamada"

inputs:
  strict:
    description: "Fail workflow on audit warnings"
    required: false
    default: "true"
  fail-on-block:
    description: "Fail workflow on policy blocks"
    required: false
    default: "true"
  export-otel:
    description: "Export audit events via OTLP gRPC endpoint"
    required: false
    default: "false"

outputs:
  verdict:
    description: "Audit status: PASS, WARN, or BLOCK"
    value: ${{ steps.audit.outputs.verdict }}
  policy-digest:
    description: "Deterministic SHA-256 policy digest"
    value: ${{ steps.audit.outputs.policy_digest }}
  violations-count:
    description: "Total number of policy violations detected"
    value: ${{ steps.audit.outputs.violations_count }}

runs:
  using: "composite"
  steps:
    - name: Run Aegis Cloud Sentinel Gate
      id: audit
      shell: bash
      env:
        ACTIONS_ID_TOKEN_REQUEST_URL: ${{ env.ACTIONS_ID_TOKEN_REQUEST_URL }}
        ACTIONS_ID_TOKEN_REQUEST_TOKEN: ${{ env.ACTIONS_ID_TOKEN_REQUEST_TOKEN }}
      run: |
        python -m aegis.cli check --ci --strict=${{ inputs.strict }}
```

---

## 4. セキュリティ、マスキング、コンテキストドリフト抑止要件

### 4.1 高特権シークレットの遮断と保護
1. **平文 OIDC トークンの漏洩防止**:
   - OIDC JWT トークン本体はメモリ上でのみデコード検証を行い、ディスク（ログファイル）には SHA-256 ダイジェストのみを記録。
2. **PR 差分内シークレットの即時検知**:
   - `GITHUB_TOKEN`、クラウドプロバイダ認証情報（`AKIA...`、`ey...`）、秘密鍵（`-----BEGIN PRIVATE KEY-----`）が差分内に混入した場合は即座に `BLOCK` 判定を発行。

### 4.2 クラウド環境におけるコンテキストドリフト抑止
- PR の Description、Issue 本文、コミットメッセージに記述された「目的」と、実際のコード変更ファイル（diff stat）の乖離度を評価。
- リポジトリ保護対象ファイル（`.github/workflows/*`、`.aegis/*`、`pyproject.toml`）をエージェントが意図せず変更した場合に `WARN` または `BLOCK` を発行。

---

## 5. 非機能要件

| 項目 | 目標値 / 仕様 |
| :--- | :--- |
| **CI 実行レイテンシ** | 差分スキャン + OIDC 検証を含め **500ms 未満** で完了すること |
| **判定決定論性** | 同一の Git コミット差分およびポリシーセットに対し、常に 100% 同一のハッシュ・判定を返すこと |
| **フォールバック耐性** | OIDC トークン取得エンドポイントが不通の場合でも、ローカル環境変数のみで gracefully に degraded audit を継続すること |
| **プラットフォーム互換性** | Linux (Ubuntu runner), macOS runner, Windows runner の全 OS で正常動作すること |
