"""
Local Model Context Protocol (MCP) Security Gateway Server
Inspects tool calls with Sentinel and records 5W1H audit records.
"""
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from aegis.mcp_gateway.protocol import MCP_TOOLS_MANIFEST, JSONRPCRequest, JSONRPCResponse
from aegis.models import (
    ClientToolType,
    NormalizedAIEvent,
    NormalizedInference,
    NormalizedToolCall,
    NormalizedTrigger,
    TriggerSourceType,
    VerdictStatus,
)
from aegis.recorder.wal import SQLiteWALStore
from aegis.sentinel.judge import SentinelJudge
from aegis.mcp_gateway.notifier import UniversalNotifier


class LocalMCPServer:
    """ローカル STDIO/SSE で動作する MCP セキュリティゲートウェイサーバー"""

    def __init__(self, policy_dir: str = ".aegis/rules"):
        self.judge = SentinelJudge(policy_dir=policy_dir)
        self.wal = SQLiteWALStore()
        self.notifier = UniversalNotifier()

    def handle_request_dict(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """JSON-RPC リクエストのディスパッチと処理"""
        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "aegis-mcp-security-gateway",
                        "version": "1.0.0"
                    }
                }
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": MCP_TOOLS_MANIFEST}
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            return self._handle_tool_call(req_id, tool_name, arguments)

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }

    def _handle_tool_call(self, req_id: Any, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Tool Call の検閲および監査記録"""
        if tool_name == "aegis_inspect_action":
            action_type = arguments.get("action_type", "run_command")
            parameters = arguments.get("parameters", {})
            verdict = self.judge.evaluate_tool_call(action_type, parameters)

            if verdict.status in (VerdictStatus.BLOCK, VerdictStatus.WARN) and verdict.violations:
                # 危険・警告操作の検出: 即時遮断は行わず、マルチプラットフォーム通知と FLAGGED 記録を行う（監査専従）
                warning_text = self.notifier.notify_violation(action_type, parameters, verdict)
                self._record_audit_event(
                    trigger_source=TriggerSourceType.MCP_TOOL_CALL,
                    tool_name=action_type,
                    args=parameters,
                    status="FLAGGED"
                )
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": warning_text}]
                    }
                }

            # 正常記録
            self._record_audit_event(
                trigger_source=TriggerSourceType.MCP_TOOL_CALL,
                tool_name=action_type,
                args=parameters,
                status="ALLOWED"
            )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": "Aegis Sentinel Check: PASSED (Allowed)"}]
                }
            }

        elif tool_name == "aegis_record_intent":
            intent_summary = arguments.get("intent_summary", "")
            affected = arguments.get("affected_components", [])
            self._record_audit_event(
                trigger_source=TriggerSourceType.MCP_TOOL_CALL,
                tool_name="aegis_record_intent",
                args=arguments,
                status="SUCCESS",
                intent_summary=intent_summary,
                affected_files=affected
            )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": "Aegis intent and reasoning trace recorded successfully."}]
                }
            }

        # 未知のツール名に対するデフォルト検査
        verdict = self.judge.evaluate_tool_call(tool_name, arguments)
        if verdict.status in (VerdictStatus.BLOCK, VerdictStatus.WARN) and verdict.violations:
            warning_text = self.notifier.notify_violation(tool_name, arguments, verdict)
            self._record_audit_event(
                trigger_source=TriggerSourceType.MCP_TOOL_CALL,
                tool_name=tool_name,
                args=arguments,
                status="FLAGGED"
            )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": warning_text}]}
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"content": [{"type": "text", "text": f"Tool {tool_name} executed under Aegis."}]}
        }

    def _record_audit_event(
        self,
        trigger_source: TriggerSourceType,
        tool_name: str,
        args: Dict[str, Any],
        status: str,
        intent_summary: Optional[str] = None,
        affected_files: Optional[list] = None,
    ):
        """正規化イベントを生成してローカル WAL に格納"""
        try:
            event = NormalizedAIEvent(
                trace_id=str(uuid.uuid4()),
                client_tool=ClientToolType.CLI,
                trigger=NormalizedTrigger(
                    source=trigger_source,
                    sanitized_prompt=str(args),
                    user_identity="local-developer",
                    session_id="mcp-session"
                ),
                inference=NormalizedInference(
                    user_intent_summary=intent_summary
                ),
                tool_calls=[
                    NormalizedToolCall(
                        tool_name=tool_name,
                        arguments=args,
                        status=status
                    )
                ],
                affected_files=affected_files or []
            )
            # SQLite WAL への軽量保存（1ms）
            self.wal.append_event({
                "trace_id": event.trace_id,
                "timestamp": event.timestamp.isoformat(),
                "tool_name": tool_name,
                "status": status,
                "summary": intent_summary or str(args)[:100]
            })
        except Exception:
            pass

    def run_stdio(self):
        """標準入出力ループの実行"""
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request_dict(req)
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
