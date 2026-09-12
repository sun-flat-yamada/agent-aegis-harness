---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "architecture_doc"
id: "SPEC-MCP-AUDIT-001"
title: "MCP セキュリティゲートウェイ監査専従化 & マルチプラットフォーム汎用通知仕様書 (Spec)"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: ".devs/changes/2026-09-12_mcp-audit-notification/spec.md"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.4.0"
tags: ["spec", "mcp", "notification", "notifier", "audit-only", "protocol"]
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
---

# MCP セキュリティゲートウェイ監査専従化 & マルチプラットフォーム汎用通知仕様書 (Spec)

**Document ID:** SPEC-MCP-AUDIT-001 | **Version:** 1.0.0 | **Status:** Active | **Author:** @sun-flat-yamada (Youhei Yamada)  
**Target Change:** `.devs/changes/2026-09-12_mcp-audit-notification`  
**Blueprint:** [`blueprint.md`](blueprint.md) | **Related Implementation:** [`src/aegis/mcp_gateway/notifier.py`](../../src/aegis/mcp_gateway/notifier.py)

---

## 1. 要求事項とドメインモデル

### 1.1 機能要件 (Functional Requirements)
1. **REQ-FUNC-001: ツール呼び出しの非遮断化 (Non-blocking Guarantee)**
   - `aegis_inspect_action` および未知のツール呼び出しにおいて、Sentinel 判定が `VerdictStatus.BLOCK` または `WARN` であっても、JSON-RPC エラー（`-32000`）を返してはならない。
   - 常に JSON-RPC 2.0 の `result` オブジェクトを返却し、エージェントが操作を継続できるようにする。
2. **REQ-FUNC-002: 5W1H 監査イベントの確実な記録 (Audit Retention)**
   - 危険操作が検出された場合、ステータスを `"FLAGGED"` としてローカル SQLite WAL に記録する。
   - 検知された違反ルール（`rule_id`）、違反メッセージ（`violations`）、対象引数を記録に含める。
3. **REQ-FUNC-003: 汎用マルチプラットフォーム通知 (Universal Notification)**
   - 危険操作検出時、即時に以下の 4 つの手段で通知を発行する：
     - **STDERR 通知**: ANSI カラー付きの強調警告メッセージ + ターミナルベル (`\a`) の出力。
     - **インバンド通知**: ツールレスポンスの `content` 内に警告テキスト（⚠️ [AEGIS SECURITY NOTICE]）を埋め込む。
     - **OS ネイティブ通知**: Windows (PowerShell Toast), macOS (osascript), Linux (notify-send) を非同期・非ブロッキングで発行。
     - **ファイルログ通知**: `.aegis/alerts.log` への追記。

### 1.2 非機能要件 (Non-Functional Requirements)
1. **REQ-NF-001: STDIO プロトコル健全性の維持 (Zero STDOUT Pollution)**
   - `sys.stdout` には JSON-RPC メッセージ以外のバイト（ログ、print 文、デバッグ出力等）を一切流してはならない。
   - すべての人間向けコンソール警告は厳密に `sys.stderr` へ限定する。
2. **REQ-NF-002: 超低遅延と非ブロッキング (Sub-millisecond Latency Impact)**
   - 通知処理による MCP ツール呼び出し応答の遅延は 5ms 以内とする。
   - OS ネイティブ通知の呼び出しは別スレッドまたは非同期サブプロセスで実行し、タイムアウト（最大 1 秒）または即時デタッチで処理する。
3. **REQ-NF-003: ゼロ・外部依存性 (Pure Python Portable Architecture)**
   - OS デスクトップ通知のために `plyer`, `notify-py` 等の外部パッケージを追加せず、Python 標準ライブラリ（`subprocess`, `platform`, `os`, `sys`, `shutil`）のみで完結させる。
   - ヘッドレス環境、SSH セッション、Docker コンテナ環境において GUI 通知が失敗した場合でも、例外をキャッチして安全に無視（Graceful Fallback）する。

---

## 2. モジュール & インターフェース仕様

### 2.1 `UniversalNotifier` クラス (`src/aegis/mcp_gateway/notifier.py`)

```python
class UniversalNotifier:
    """
    マルチプラットフォーム・マルチクライアント対応の汎用セキュリティ通知エンジン。
    Win/Mac/Linux、および VS Code / Copilot CLI / Claude Code / ターミナル / SSH 環境に対応。
    """
    def __init__(self, alert_log_path: str = ".aegis/alerts.log"):
        self.alert_log_path = Path(alert_log_path)

    def notify_violation(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        verdict: SentinelVerdict,
    ) -> str:
        """
        危険な操作が検出された際に、多層通知を発行する。
        
        Args:
            tool_name: 呼び出されたツール名
            arguments: ツール引数
            verdict: SentinelJudge の判定結果
            
        Returns:
            str: ツールレスポンス本文に埋め込むインバンド警告メッセージ
        """
        ...
```

### 2.2 レイヤー別実装仕様

#### Layer 1: STDERR & Terminal Attention
- **フォーマット**:
  ```text
  \n\033[1;33m[AEGIS AUDIT NOTICE]\033[0m \033[1;31m⚠️ Potential Dangerous Operation Detected!\033[0m
  Rule: <rule_ids>
  Tool: <tool_name>
  Reason: <violations>
  Status: \033[1;32mExecution NOT blocked (Audit-only mode)\033[0m\a\n
  ```
- **ベル制御**: 末尾に `\a` (ASCII BEL 0x07) を付与し、ターミナルエミュレータのアテンション（タスクバー点滅、ベル音）をトリガー。

#### Layer 2: MCP インバンドレスポンス
- **戻り値テキスト**:
  ```text
  ⚠️ [AEGIS AUDIT WARNING] Dangerous operation detected by Aegis Sentinel:
  - Violations: <violation_messages>
  - Policy: <rule_ids>
  Note: This operation was NOT blocked and was permitted to execute under audit supervision.
  ```

#### Layer 3: OS ネイティブ通知 (バックグラウンド非同期)
- **Windows**:
  PowerShell コマンドレットを用いたトースト/バルーン通知の発行：
  ```powershell
  [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] ...
  ```
  またはシンプルな PowerShell 非同期バルーン通知スクリプト。
- **macOS**:
  ```bash
  osascript -e 'display notification "<message>" with title "Aegis Security Warning" sound name "Ping"'
  ```
- **Linux**:
  `shutil.which("notify-send")` でバイナリの存在を確認し、
  ```bash
  notify-send -u critical "Aegis Security Warning" "<message>"
  ```
- **エラー処理**: すべてのサブプロセス呼び出しは `try...except Exception` で保護し、失敗しても一切エラーを上げない。

#### Layer 4: 永続化アラートファイル
- 保存先: `.aegis/alerts.log` (存在しない場合はディレクトリを自動作成)
- 追記フォーマット:
  ```text
  [YYYY-MM-DDTHH:MM:SS.mmmmmm] [TOOL_NAME] [SEVERITY] <rule_id>: <message> | args: <args_summary>
  ```

---

## 3. `LocalMCPServer` との統合仕様

### 3.1 `_handle_tool_call` の挙動変更
```python
# 変更前 (旧実装: 即時遮断)
if verdict.status == VerdictStatus.BLOCK:
    violations = [v.message for v in verdict.violations]
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": err_msg}}

# 変更後 (新実装: 監査専従 & 通知)
if verdict.status in (VerdictStatus.BLOCK, VerdictStatus.WARN) and verdict.violations:
    # 1. マルチプラットフォーム通知の発行
    warning_msg = self.notifier.notify_violation(action_type, parameters, verdict)
    
    # 2. FLAGGED 監査イベントとして WAL に記録
    self._record_audit_event(
        trigger_source=TriggerSourceType.MCP_TOOL_CALL,
        tool_name=action_type,
        args=parameters,
        status="FLAGGED"
    )
    
    # 3. 正常レスポンス (result) として警告メッセージを返却
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "content": [{"type": "text", "text": warning_msg}]
        }
    }
```
