---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "architecture_doc"
id: "WALKTHROUGH-MCP-AUDIT-001"
title: "MCP セキュリティゲートウェイ監査専従化 & マルチプラットフォーム汎用通知事後検証エビデンス (Walkthrough)"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: ".devs/changes/2026-09-12_mcp-audit-notification/walkthrough.md"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.4.0"
tags: ["walkthrough", "evidence", "mcp-gateway", "notification", "verification"]
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
---

# MCP セキュリティゲートウェイ監査専従化 & マルチプラットフォーム汎用通知事後検証エビデンス (Walkthrough)

**Document ID:** WALKTHROUGH-MCP-AUDIT-001 | **Version:** 1.0.0 | **Status:** Active | **Author:** @sun-flat-yamada (Youhei Yamada)  
**Target Change:** `.devs/changes/2026-09-12_mcp-audit-notification`  
**Blueprint:** [`blueprint.md`](blueprint.md) | **Spec:** [`spec.md`](spec.md) | **Plan:** [`plan.md`](plan.md) | **Implementation:** [`implementation.md`](implementation.md)

---

## 1. 実施された変更一覧

| 区分 | ファイルパス | 主な変更内容 |
| :--- | :--- | :--- |
| **NEW** | `src/aegis/mcp_gateway/notifier.py` | `UniversalNotifier` クラスの実装。4 層ハイブリッド通知（STDERR+BEL, インバンドToolResponse, OSネイティブToast, 永続アラートログ）を提供。 |
| **MODIFY** | `src/aegis/mcp_gateway/server.py` | `LocalMCPServer._handle_tool_call` において、`VerdictStatus.BLOCK` / `WARN` 判定時の JSON-RPC エラーによる即時遮断を廃止。通知発行・`FLAGGED` 監査イベント記録・警告メッセージ付き `result` 返却に刷新。 |
| **MODIFY** | `src/aegis/cli.py` | `aah mcp-server --test` のセルフテストロジックを、遮断検証から「危険操作の検知通知 & 非遮断正常応答」の検証へ更新。 |
| **MODIFY** | `docs/setup/target-project-guide.ja.md` | 「第 4 層: MCP セキュリティゲートウェイ検査」の解説を「即時遮断」から「監査専従（Audit-Only）およびマルチプラットフォーム汎用通知」へ改訂。Line 95 の補足も更新。 |
| **MODIFY** | `docs/setup/target-project-guide.md` | 英語版ガイドの Layer 4 記述を日本語版と同期改訂。 |
| **MODIFY** | `tests/test_mcp_gateway.py` | `test_mcp_inspect_action_flagged_not_blocked`, `test_mcp_unknown_tool_flagged_not_blocked`, `test_universal_notifier_layers` 等のテストを追加・改訂。 |

---

## 2. 自動テスト結果 (Automated Test Execution)

### 2.1 MCP ゲートウェイ単体テスト (`tests/test_mcp_gateway.py`)
```text
$ python -m pytest tests/test_mcp_gateway.py
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-8.0.2, pluggy-1.6.0
rootdir: V:\repos\sun.flat.yamada\agent-aegis-harness
configfile: pyproject.toml
collected 6 items

tests\test_mcp_gateway.py ......                                         [100%]

======================== 6 passed, 1 warning in 1.57s =========================
```

### 2.2 全体テストスイート (`pytest`)
```text
$ python -m pytest
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-8.0.2, pluggy-1.6.0
rootdir: V:\repos\sun.flat.yamada\agent-aegis-harness
configfile: pyproject.toml
testpaths: tests
collected 55 items

tests\test_archivist.py ....                                             [  7%]
tests\test_azure_exporter.py ..                                          [ 10%]
tests\test_cli.py .......                                                [ 23%]
tests\test_cloud_audit.py .........                                      [ 40%]
tests\test_git_correlator.py ..                                          [ 43%]
tests\test_harvester.py ..                                               [ 47%]
tests\test_injector.py ...                                               [ 52%]
tests\test_mcp_gateway.py ......                                         [ 63%]
tests\test_merkle.py .....                                               [ 72%]
tests\test_micro_chain.py ...                                            [ 78%]
tests\test_recorder.py ..                                                [ 81%]
tests\test_refiner.py ...                                                [ 87%]
tests\test_sentinel.py ...                                               [ 92%]
tests\test_wal.py ..                                                     [ 96%]
tests\test_weekly_report.py ..                                           [100%]

======================== 55 passed, 1 warning in 4.50s ========================
```

---

## 3. CLI 実機検証ログ

### 3.1 `aah mcp-server --test` (セルフテスト検証)
```text
$ python -m aegis.cli mcp-server --test
[TEST] Testing Aegis MCP Security Gateway...
  - Safe command test: PASSED

[AEGIS AUDIT NOTICE] ⚠️ Potential Dangerous Operation Detected!
  Tool    : run_command
  Policy  : RULE-SEC-001
  Reason  : Blocked dangerous command: Dangerous root recursive file deletion command detected
  Status  : Execution NOT blocked (Audit-only mode) 
  - Dangerous command audit & notification: NOTIFIED & ALLOWED (Audit-Only Correct)
[OK] MCP Security Gateway self-test passed.
```

### 3.2 `aah check` (Sentinel Instant Audit ガバナンス検査)
```text
$ python -m aegis.cli check
[AUDIT] Running Sentinel Instant Audit...
                             Sentinel Audit Verdict                             
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Category                      ┃ Status ┃ Details                             ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ PII / Secret Redactor         │ PASSED │ Pattern rules active (0 leaks in    │
│                               │        │ git staged)                         │
│ Context Drift Integrity       │ PASSED │ Compaction drift score: 0.04        │
│                               │        │ (Threshold: 0.20)                   │
│ Instruction Pointer Integrity │ PASSED │ All 4 active instruction pointers   │
│                               │        │ verified                            │
│ Policy Digest Match           │ PASSED │ sha256:ed961461c97fdd12b64b840af60… │
│                               │        │ (5 policies)                        │
│ Skill Tool Whitelist          │ PASSED │ 10 tools approved in                │
│                               │        │ .aegis/rules/skill-compliance-poli… │
│ Cryptographic Log Chain       │ PASSED │ 12 blocks cryptographically         │
│                               │        │ verified                            │
└───────────────────────────────┴────────┴─────────────────────────────────────┘
[OK] All Sentinel Instant Audit gates passed.
```

---

## 4. 総括
本改修により、MCP セキュリティゲートウェイは「独断でユーザー操作を遮断する」アンチパターンを完全に脱却し、**「非遮断による自律エージェントの処理継続性」** と **「4 層ハイブリッド通知による人間への確実な危険周知」** を両立する堅牢な監査専従アーキテクチャへと進化しました。
すべてのテストおよび実機セルフテストが成功し、エビデンスが正常に封印されました。
