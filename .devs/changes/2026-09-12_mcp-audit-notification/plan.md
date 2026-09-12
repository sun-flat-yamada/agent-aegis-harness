---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "architecture_doc"
id: "PLAN-MCP-AUDIT-001"
title: "MCP セキュリティゲートウェイ監査専従化 & マルチプラットフォーム汎用通知開発計画書 (Plan)"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: ".devs/changes/2026-09-12_mcp-audit-notification/plan.md"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.4.0"
tags: ["plan", "wbs", "testing", "mcp", "notification"]
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
---

# MCP セキュリティゲートウェイ監査専従化 & マルチプラットフォーム汎用通知開発計画書 (Plan)

**Document ID:** PLAN-MCP-AUDIT-001 | **Version:** 1.0.0 | **Status:** Active | **Author:** @sun-flat-yamada (Youhei Yamada)  
**Target Change:** `.devs/changes/2026-09-12_mcp-audit-notification`  
**Blueprint:** [`blueprint.md`](blueprint.md) | **Spec:** [`spec.md`](spec.md)

---

## 1. 開発方針と原則

1. **完全な非遮断性 (Zero-Disruption)**:
   いかなる Sentinel 違反検出時も JSON-RPC エラーによるツール呼び出し停止を絶対に行わない。
2. **多重防御ならぬ多重通知 (Multi-Layer Notification)**:
   OS、実行ホスト、ターミナル、エディタ、ログファイルのいずれの経路でも、確実にユーザーへ危険操作の兆候を届ける。
3. **STDOUT 完全保護 (Strict Protocol Compliance)**:
   MCP STDIO セッションにおいて、`sys.stdout` への無関係な出力（標準 print 等）を厳禁とし、プロトコルエラーを未然に防止する。

---

## 2. タスク詳細 WBS (Work Breakdown Structure)

| Phase | Task ID | タスク概要 | 対象ファイル | 完了基準 |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | T-01 | `UniversalNotifier` モジュールの実装 | `src/aegis/mcp_gateway/notifier.py` | STDERR+BEL、OS Native Toast、ファイル追記、インバンド文字列生成が単体動作すること |
| **Phase 2** | T-02 | `LocalMCPServer` の非遮断・通知統合 | `src/aegis/mcp_gateway/server.py` | BLOCK 判定時にエラー返却せず、通知を発行して result を返すこと |
| **Phase 3** | T-03 | CLI セルフテストの更新 | `src/aegis/cli.py` | `aah mcp-server --test` が非遮断・警告検知仕様で成功すること |
| **Phase 4** | T-04 | ドキュメントの改訂 | `docs/setup/target-project-guide.ja.md`<br/>`docs/setup/target-project-guide.md` | 「即時遮断」から「監査専従・マルチプラットフォーム通知」への記載改訂 |
| **Phase 5** | T-05 | 単体テスト・統合テストの改訂 & 実行 | `tests/test_mcp_gateway.py` | `python -m pytest` 全テスト成功（新テスト含む） |
| **Phase 6** | T-06 | 事後検証エビデンスの封印 | `walkthrough.md` | 実機ログ、テスト結果、差分を記録して封印 |

---

## 3. テスト・検証戦略

### 3.1 単体テスト (`tests/test_mcp_gateway.py`)
- `test_mcp_inspect_action_allowed`: 正常コマンドが従来どおり PASSED となること。
- `test_mcp_inspect_action_flagged_not_blocked`: 危険コマンド（`rm -rf /`）が遮断されず、`result` が返り、インバンドテキストに警告が含まれること。
- `test_universal_notifier_layers`: `UniversalNotifier` の各レイヤー（STDERR, ファイル追記, OS通知の例外耐性）が正常に機能すること。

### 3.2 CLI 実機検証
- `python -m aegis.cli mcp-server --test`
- 危険コマンドに対する STDERR 警告およびターミナルベル (`\a`) の送出確認。
- `.aegis/alerts.log` への追記確認。

---

## 4. リスク評価と緩和策

| リスク | 影響度 | 発生確率 | 緩和策 |
| :--- | :---: | :---: | :--- |
| OS ネイティブ通知の呼び出しによるプロセスブロック | 高 | 中 | `threading.Thread(daemon=True)` または非ブロッキング `subprocess.Popen` を採用し、メインスレッドをブロックしない。 |
| GUI のない環境（CI/SSH）での例外クラッシュ | 高 | 高 | OS 通知実行部を広範な `try...except Exception` で囲み、エラー発生時も黙ってスキップ（Graceful Degradation）。 |
| `sys.stdout` への誤出力による JSON-RPC 破壊 | 極大 | 低 | 通知メッセージの出力先を明示的に `sys.stderr` に固定し、コードレビューで `print()` の使用を完全排除。 |
