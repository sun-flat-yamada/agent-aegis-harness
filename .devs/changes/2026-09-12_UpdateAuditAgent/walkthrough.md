---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "architecture_doc"
id: "WALKTHROUGH-AUDIT-AGENT-001"
title: "Agent Aegis Harness (aah) - Multi-AI Automated Audit Collection Verification Walkthrough"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: "docs/WALKTHROUGH_UPDATE_AUDIT_AGENT.md"
hash_digest: "sha256:pending"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "windsurf", "aws-kiro", "cli"]
  min_aah_version: "0.3.0"
tags: ["walkthrough", "verification", "evidence", "mcp-gateway", "harvester", "non-destructive"]
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
---

# Agent Aegis Harness (aah) - マルチAI自動監査記録・収集基盤 検証エビデンス (Walkthrough)

**Document ID:** WALKTHROUGH-AUDIT-AGENT-001 | **Version:** 1.0.0 | **Status:** Active | **Author:** @sun-flat-yamada (Youhei Yamada)  
**Target Change:** `.devs/changes/2026-09-12_UpdateAuditAgent`

---

## 1. 実施された変更一覧

本変更では、日々の開発者による多様な AI ツール（VSCode Copilot, Claude Code, AWS Kiro, Cursor 等）の利用から、手動操作なしで自動的に監査証跡を収集・暗号封印するハイブリッド二重捕捉基盤（DVAA）を実装しました。

### 1.1 作成・更新されたモジュール一覧

| ファイルパス | 変更種別 | 主な実装内容 |
| :--- | :--- | :--- |
| `src/aegis/models.py` | [MODIFY] | `NormalizedAIEvent`, `TriggerSourceType`, `NormalizedTrigger`, `NormalizedInference`, `NormalizedToolCall`, `GitCorrelationContext` の追加。 |
| `.aegis/instructions/aegis-system-governance.md` | [NEW] | 全社共通の 5W1H 監査説明責任、シークレット禁止、禁止コマンド遮断規約。 |
| `.aegis/instructions/aegis-claude-rules.md` | [NEW] | Claude Code 向け推論トレース・MCP 利用規約。 |
| `.aegis/instructions/aegis-copilot-rules.md` | [NEW] | VSCode Copilot 向けコミット前検証・チャットセッション相関規約。 |
| `src/aegis/injector/templates.py` | [NEW] | 既存ファイル破壊防止用マーカー (`<!-- AEGIS-AUDIT-INJECTION -->`) および各ツール用ポインタ定義。 |
| `src/aegis/injector/engine.py` | [NEW] | 既存ファイルの末尾に 1 行の参照ポインタのみを追記する非破壊インジェクションエンジン（冪等性保証）。 |
| `src/aegis/injector/__init__.py` | [NEW] | インジェクターパッケージのエクスポート定義。 |
| `src/aegis/mcp_gateway/protocol.py` | [NEW] | MCP ツールマニフェスト (`aegis_inspect_action`, `aegis_record_intent`) および JSON-RPC 2.0 型定義。 |
| `src/aegis/mcp_gateway/server.py` | [NEW] | STDIO/SSE で動作する Local MCP セキュリティゲートウェイサーバー（Sentinel 即時検閲）。 |
| `src/aegis/mcp_gateway/client.py` | [NEW] | Cloud MCP 転送クライアントおよびネットワーク障害時の自動ローカルフォールバック機構。 |
| `src/aegis/mcp_gateway/__init__.py` | [NEW] | MCP ゲートウェイパッケージのエクスポート定義。 |
| `src/aegis/recorder/git_correlator.py` | [NEW] | Git `pre-commit`（シークレット検査）および `post-commit`（AI セッションハッシュ相関）フック。 |
| `src/aegis/harvester/claude.py` | [NEW] | Claude Code セッション JSONL パーサー & 正規化変換エンジン。 |
| `src/aegis/harvester/watcher.py` | [NEW] | セッションディレクトリ変更検知ハーベスター。 |
| `src/aegis/recorder/wal.py` | [MODIFY] | `SQLiteWALStore` エイリアス、`get_latest_record_hash()` メソッドの追加。 |
| `src/aegis/cli.py` | [MODIFY] | `aah init --tools`, `aah mcp-server [--test]`, `aah status` コマンドの実装。 |
| `docs/setup/cloud-mcp-server-guide.ja.md` | [NEW] | Cloud MCP Security Gateway 構築・運用手順書（日本語版）。 |
| `docs/setup/cloud-mcp-server-guide.md` | [NEW] | Cloud MCP Security Gateway 構築・運用手順書（英語正本）。 |

---

## 2. 自動テスト検証ログ

新規追加された 11 件のテストを含む、全 37 件のテストスイートが正常にパスしました。

### 実行コマンド
```bash
python -m pytest tests/ -v
```

### 実行結果ログ
```text
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-8.0.2, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: V:\repos\sun.flat.yamada\agent-aegis-harness
configfile: pyproject.toml
collecting ... collected 37 items / 1 skipped

tests/test_archivist.py::test_policy_hasher_deterministic PASSED         [  2%]
tests/test_archivist.py::test_policy_hasher_detects_modification PASSED  [  5%]
tests/test_archivist.py::test_hash_chain_signing_and_verification PASSED [  8%]
tests/test_archivist.py::test_hash_chain_tamper_detection PASSED         [ 10%]
tests/test_azure_exporter.py::test_azure_exporter_batch_success PASSED   [ 13%]
tests/test_azure_exporter.py::test_azure_exporter_batch_failure_retry PASSED [ 16%]
tests/test_git_correlator.py::test_git_pre_commit_secret_blocking PASSED [ 18%]
tests/test_git_correlator.py::test_git_pre_commit_clean_pass PASSED      [ 21%]
tests/test_harvester.py::test_claude_session_parser_user_prompt PASSED   [ 24%]
tests/test_harvester.py::test_claude_session_parser_assistant_thinking_and_tool PASSED [ 27%]
tests/test_injector.py::test_non_destructive_append PASSED               [ 29%]
tests/test_injector.py::test_injector_idempotency PASSED                 [ 32%]
tests/test_injector.py::test_inject_all_tools PASSED                     [ 35%]
tests/test_mcp_gateway.py::test_mcp_initialize_and_tools_list PASSED     [ 37%]
tests/test_mcp_gateway.py::test_mcp_inspect_action_allowed PASSED        [ 40%]
tests/test_mcp_gateway.py::test_mcp_inspect_action_blocked PASSED        [ 43%]
tests/test_mcp_gateway.py::test_cloud_mcp_fallback PASSED                [ 45%]
tests/test_merkle.py::test_merkle_tree_construction_even PASSED          [ 48%]
tests/test_merkle.py::test_merkle_tree_construction_odd PASSED           [ 51%]
tests/test_merkle.py::test_merkle_proof_tamper PASSED                    [ 54%]
tests/test_merkle.py::test_merkle_large_scale_performance PASSED         [ 56%]
tests/test_merkle.py::test_audit_notary_ledger PASSED                    [ 59%]
tests/test_micro_chain.py::test_micro_chain_normal_flow PASSED           [ 62%]
tests/test_micro_chain.py::test_micro_chain_tamper_payload PASSED        [ 64%]
tests/test_micro_chain.py::test_micro_chain_tamper_reorder PASSED        [ 67%]
tests/test_recorder.py::test_recorder_dual_stream_writes_and_verifies PASSED [ 70%]
tests/test_recorder.py::test_recorder_independent_hash_chains_across_sessions PASSED [ 72%]
tests/test_refiner.py::test_cluster_analyzer_empty_log PASSED            [ 75%]
tests/test_refiner.py::test_cluster_analyzer_parses_violations PASSED    [ 78%]
tests/test_refiner.py::test_patch_proposer_generates_recommendations PASSED [ 81%]
tests/test_sentinel.py::test_sensitive_redactor_masks_credentials PASSED [ 83%]
tests/test_sentinel.py::test_sensitive_redactor_nested_dict PASSED       [ 86%]
tests/test_sentinel.py::test_sentinel_blocks_dangerous_commands PASSED   [ 89%]
tests/test_wal.py::test_wal_enqueue_and_fetch PASSED                     [ 91%]
tests/test_wal.py::test_wal_concurrency PASSED                           [ 94%]
tests/test_weekly_report.py::test_weekly_governance_report_aggregation PASSED [ 97%]
tests/test_weekly_report.py::test_weekly_governance_report_footnotes_rendering PASSED [100%]

================== 37 passed, 1 skipped, 1 warning in 2.34s ===================
```

---

## 3. CLI 実機検証エビデンス

### 3.1 MCP Security Gateway 自己診断 (`aah mcp-server --test`)
```text
$ python -m aegis.cli mcp-server --test
[TEST] Testing Aegis MCP Security Gateway...
  - Safe command test: PASSED
  - Dangerous command block: BLOCKED (Correct)
[OK] MCP Security Gateway self-test passed.
```

### 3.2 非破壊インジェクション & 冪等性検証 (`aah init --tools=all`)
1 回目の実行時（ポインタ作成）：
```text
$ python -m aegis.cli init --tools=all
[OK] Initializing agent-aegis-harness in repository...
  - claude pointer: CREATED_NEW
  - copilot pointer: CREATED_NEW
  - amazon_q pointer: CREATED_NEW
  - cursor pointer: CREATED_NEW
Policy Bundle Digest: sha256:ed961461c97fdd12b64b840af601720163152ff3a0c550eb81aac5dac1179f76
[OK] Setup complete. Run aah check to verify.
```

2 回目の実行時（二重追記の防止とスキップ）：
```text
$ python -m aegis.cli init --tools=all
[OK] Initializing agent-aegis-harness in repository...
  - claude pointer: SKIPPED_ALREADY_INJECTED
  - copilot pointer: SKIPPED_ALREADY_INJECTED
  - amazon_q pointer: SKIPPED_ALREADY_INJECTED
  - cursor pointer: SKIPPED_ALREADY_INJECTED
Policy Bundle Digest: sha256:ed961461c97fdd12b64b840af601720163152ff3a0c550eb81aac5dac1179f76
[OK] Setup complete. Run aah check to verify.
```

### 3.3 計装ステータス確認 (`aah status`)
```text
$ python -m aegis.cli status
                    Aegis Multi-AI Instrumentation Status                     
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Component              ┃ Target / Mode                   ┃ Status          ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ Claude Code Pointer    │ CLAUDE.md                       │ ACTIVE          │
│ VSCode Copilot Pointer │ .github/copilot-instructions.md │ ACTIVE          │
│ AWS Kiro / Q Pointer   │ .amazonq/rules.md               │ ACTIVE          │
│ Cursor Pointer         │ .cursorrules                    │ ACTIVE          │
│ MCP Gateway            │ Local (Default: STDIO)          │ READY           │
│ Local SQLite WAL       │ aegis_wal.db                    │ READY (Genesis) │
└────────────────────────┴─────────────────────────────────┴─────────────────┘
```

### 3.4 監査完全性検証 (`aah check`)
```text
$ python -m aegis.cli check
[AUDIT] Running Sentinel Instant Audit...
                             Sentinel Audit Verdict                             
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Category                ┃ Status ┃ Details                                   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ PII / Secret Redactor   │ PASSED │ Pattern rules active (0 leaks in git      │
│                         │        │ staged)                                   │
│ Context Drift Integrity │ PASSED │ Compaction drift score: 0.04 (Threshold:  │
│                         │        │ 0.20)                                     │
│ Policy Digest Match     │ PASSED │ sha256:ed961461c97fdd12b64b840af60172016… │
│                         │        │ (5 policies)                              │
│ Skill Tool Whitelist    │ PASSED │ 10 tools approved in                      │
│                         │        │ .aegis/rules/skill-compliance-policy.yaml │
│ Cryptographic Log Chain │ PASSED │ 3 blocks cryptographically verified       │
└─────────────────────────┴────────┴───────────────────────────────────────────┘
[OK] All Sentinel Instant Audit gates passed.
```

---

## 4. 結論

本変更により、被監査プロジェクトへの `aah init` 適用後、開発者が普段どおりに VSCode Copilot、Claude Code、AWS Kiro などを利用するだけで、手動操作不要で 5W1H 監査記録が安全に保存・収集・暗号封印されるハイブリッド監査基盤が完成しました。すべての設計要件、自動テスト、および実機検証が完全に充足されています。
