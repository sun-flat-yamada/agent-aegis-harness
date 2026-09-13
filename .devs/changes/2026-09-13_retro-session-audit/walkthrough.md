---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "architecture_doc"
id: "SPEC-RETRO-005"
title: "Retroactive Local AI Session Harvester & Audit Correlator Walkthrough & Evidence"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: ".devs/changes/2026-09-13_retro-session-audit/walkthrough.md"
hash_digest: "sha256:pending"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor"]
  min_aah_version: "0.1.0"
tags: ["walkthrough", "evidence", "pytest", "cli-verification", "retroactive-audit"]
author: "@sun-flat-yamada"
last_reviewed: "2026-09-13"
---

# 事後実証エビデンスレポート: ローカル AI セッション後追い監査・相関ツール

## 1. 実施された変更一覧

| 変更種別 | ファイルパス | 役割・変更概要 |
|:---:|:---|:---|
| **[MODIFY]** | [`src/aegis/models.py`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/src/aegis/models.py) | `ForensicProvenance` モデル追加、`GitCorrelationContext` 拡張、`NormalizedAIEvent` への `extraction_method` / `tags` / `forensic_provenance` フィールド追加 |
| **[MODIFY]** | [`src/aegis/sentinel/redactor.py`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/src/aegis/sentinel/redactor.py) | OpenAI の最新キー仕様 (`sk-proj-...`) に対応したマスキング正規表現の強化 |
| **[NEW]** | [`src/aegis/harvester/copilot_parser.py`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/src/aegis/harvester/copilot_parser.py) | VS Code Fast-append Delta JSONL (Kind 0/1/2) 仮想リプレイエンジン & イベント抽出 |
| **[NEW]** | [`src/aegis/harvester/git_correlator.py`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/src/aegis/harvester/git_correlator.py) | Git コミット・PR 多層相関スコアリングエンジン (時間近接度、ファイル重複、意図類似度) |
| **[NEW]** | [`src/aegis/harvester/discoverer.py`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/src/aegis/harvester/discoverer.py) | VS Code / Claude / Cursor のローカルセッション自動探索ディスカバラー |
| **[NEW]** | [`src/aegis/harvester/retro_auditor.py`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/src/aegis/harvester/retro_auditor.py) | 探索・パース・相関・諸元タグ付け・WAL/ハッシュチェーン集積オーケストレーター |
| **[MODIFY]** | [`src/aegis/harvester/__init__.py`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/src/aegis/harvester/__init__.py) | 新規モジュール群のエクスポート |
| **[MODIFY]** | [`src/aegis/cli.py`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/src/aegis/cli.py) | `aah harvest retro` および `aah audit-retro` CLI コマンドの追加と Rich レポート表示 |
| **[NEW]** | [`tests/test_retro_harvester.py`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/tests/test_retro_harvester.py) | Delta リプレイ、シークレットマスキング、Git 相関、End-to-End 完全性集積テスト |

---

## 2. 自動テスト実行結果 (pytest)

新規作成した `test_retro_harvester.py` を含む全テストスイート（59 件）がオールグリーンで通過しました。

```text
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-9.1.1, pluggy-1.6.0
rootdir: V:\repos\sun.flat.yamada\agent-aegis-harness
configfile: pyproject.toml
testpaths: tests
plugins: asyncio-1.4.0
asyncio: mode=auto, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 59 items

tests\test_archivist.py ....                                             [  6%]
tests\test_azure_exporter.py ..                                          [ 10%]
tests\test_cli.py .......                                                [ 22%]
tests\test_cloud_audit.py .........                                      [ 37%]
tests\test_git_correlator.py ..                                          [ 40%]
tests\test_harvester.py ..                                               [ 44%]
tests\test_injector.py ...                                               [ 49%]
tests\test_mcp_gateway.py ......                                         [ 59%]
tests\test_merkle.py .....                                               [ 67%]
tests\test_micro_chain.py ...                                            [ 72%]
tests\test_recorder.py ..                                                [ 76%]
tests\test_refiner.py ...                                                [ 81%]
tests\test_retro_harvester.py ....                                       [ 88%]
tests\test_sentinel.py ...                                               [ 93%]
tests\test_wal.py ..                                                     [ 96%]
tests\test_weekly_report.py ..                                           [100%]

============================= 59 passed in 3.45s ==============================
```

---

## 3. 実機ストレージ探索 & CLI 実行エビデンス

### 3.1 実リポジトリ (`local-llm-kit`) 照合と Git 相関検証
```text
PS V:\repos\sun.flat.yamada\agent-aegis-harness> .\.venv\Scripts\python -m aegis.cli harvest retro --repo v:\repos\sun.flat.yamada\local-llm-kit --matched-only --dry-run
[RETRO AUDIT] Starting retroactive local AI session discovery...
  Target Repository: V:\repos\sun.flat.yamada\local-llm-kit
  Tool Filter: all | Ingest: False | Git Correlation: True
    Aegis Retroactive AI Session Audit Summary    
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric                   ┃ Count / Status      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ Discovered Session Files │ 48                  │
│ Matched Workspace Files  │ 8                   │
│ Extracted AI Turn Events │ 15                  │
│ Git Correlated Commits   │ 1                   │
│ Linked Pull Requests     │ 0                   │
│ Ingestion Mode           │ DRY-RUN (Simulated) │
└──────────────────────────┴─────────────────────┘
```

### 3.2 実機集積実行 (`--ingest`)
```text
PS V:\repos\sun.flat.yamada\agent-aegis-harness> .\.venv\Scripts\python -m aegis.cli harvest retro --ingest
[RETRO AUDIT] Starting retroactive local AI session discovery...
  Target Repository: V:\repos\sun.flat.yamada\agent-aegis-harness
  Tool Filter: all | Ingest: True | Git Correlation: True
   Aegis Retroactive AI Session Audit Summary    
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Metric                       ┃ Count / Status ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ Discovered Session Files     │ 48             │
│ Matched Workspace Files      │ 48             │
│ Extracted AI Turn Events     │ 64             │
│ Git Correlated Commits       │ 0              │
│ Linked Pull Requests         │ 0              │
│ Ingested into SQLite WAL     │ 64             │
│ Sealed into Hash-Chain Trail │ 64             │
└──────────────────────────────┴────────────────┘
[OK] Retroactive events securely sealed into Aegis Hash Chain. Run aah verify to attest integrity.
```

### 3.3 ハッシュチェーン完全性検証 (`aah verify`)
```text
PS V:\repos\sun.flat.yamada\agent-aegis-harness> .\.venv\Scripts\python -m aegis.cli verify
[VERIFY] Verifying audit log integrity: .aegis/logs/audit-trail.jsonl...
[OK] Cryptographic proof verified. All 82 audit blocks intact. No tampering detected.
```

### 3.4 Sentinel Instant Audit ゲート評価 (`aah check`)
```text
PS V:\repos\sun.flat.yamada\agent-aegis-harness> .\.venv\Scripts\python -m aegis.cli check
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
│ Cryptographic Log Chain       │ PASSED │ 82 blocks cryptographically         │
│                               │        │ verified                            │
└───────────────────────────────┴────────┴─────────────────────────────────────┘
[OK] All Sentinel Instant Audit gates passed.
```

---

## 4. データの諸元およびプロベナンスタグの実機記録例

集積されたログブロック内の諸元メタデータ構造：
```json
{
  "trace_id": "dc4be854-d042-42a7-985d-4c88a303ea1e",
  "extraction_method": "retro_local_discovery",
  "tags": [
    "source:github-copilot",
    "extraction:retroactive",
    "session:dc4be854-d042-42a7-985d-4c88a303ea1e",
    "uri:sun.flat.yamada",
    "git:unlinked"
  ],
  "forensic_provenance": {
    "source_path": "C:\\Users\\sun_flat\\AppData\\Roaming\\Code\\User\\workspaceStorage\\7bfeb89190d27d8ffe8480e9caf5dacd\\chatSessions\\dc4be854-d042-42a7-985d-4c88a303ea1e.jsonl",
    "source_sha256": "4d2ba25db78f1e2bbefbfec5982c8a4f37bc9c5c030ee0a720acf75b6a5567fc",
    "parser_id": "copilot-delta-v1",
    "extraction_timestamp": "2026-09-13T11:16:23.682853",
    "confidence_level": "MEDIUM",
    "raw_record_kind": null
  },
  "git_context": {
    "commit_sha": null,
    "branch_name": "main",
    "confidence_score": 0.063,
    "confidence_level": "UNLINKED"
  },
  "integrity": {
    "previous_record_hash": "5d53c45732eb54373243f074358d66cb94dfffca1f5c482504e9e1f87af0a523",
    "current_record_hash": "c02ecb2de28c41e41eb62ab209e3f9bb14d5749087dbac7521e2b3ec529abf7e"
  }
}
```

---

## 5. 結論
要求された「GitHub Copilot などのローカルセッション後追い監査ツール」、「本来の収集と同形式での集積」、「抽出諸元のタグ付け識別」、「Git commit/PR との多層相関紐付け」、「最新知見の反映」の全要件が実機において完全に達成され、暗号学的改ざん防止台帳へ封印されました。
