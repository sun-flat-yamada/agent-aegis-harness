"""
Tests for Aegis MCP Security Gateway (Local, UniversalNotifier, and Cloud Fallback)
"""
import io
import sys
from pathlib import Path
import pytest
from aegis.mcp_gateway.server import LocalMCPServer
from aegis.mcp_gateway.client import CloudMCPClient
from aegis.mcp_gateway.notifier import UniversalNotifier
from aegis.sentinel.judge import SentinelJudge


def test_mcp_initialize_and_tools_list():
    """MCP の初期化とツール一覧取得のテスト"""
    server = LocalMCPServer()

    init_resp = server.handle_request_dict({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert init_resp["result"]["serverInfo"]["name"] == "aegis-mcp-security-gateway"

    list_resp = server.handle_request_dict({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tool_names = [t["name"] for t in list_resp["result"]["tools"]]
    assert "aegis_inspect_action" in tool_names
    assert "aegis_record_intent" in tool_names


def test_mcp_inspect_action_allowed():
    """安全なコマンドの検閲通過テスト"""
    server = LocalMCPServer()
    req = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {
            "name": "aegis_inspect_action",
            "arguments": {
                "action_type": "run_command",
                "parameters": {"CommandLine": "pytest tests/"}
            }
        }
    }
    resp = server.handle_request_dict(req)
    assert "result" in resp
    assert "PASSED" in resp["result"]["content"][0]["text"]


def test_mcp_inspect_action_flagged_not_blocked():
    """危険なコマンドの監査通知・非遮断テスト (Audit-Only Mode)"""
    server = LocalMCPServer()
    req = {
        "jsonrpc": "2.0",
        "id": 11,
        "method": "tools/call",
        "params": {
            "name": "aegis_inspect_action",
            "arguments": {
                "action_type": "run_command",
                "parameters": {"CommandLine": "rm -rf /"}
            }
        }
    }
    resp = server.handle_request_dict(req)
    # 監査専従のため error による遮断は行わず、result を返却すること
    assert "error" not in resp
    assert "result" in resp
    content_text = resp["result"]["content"][0]["text"]
    assert "AEGIS AUDIT WARNING" in content_text
    assert "NOT blocked" in content_text
    assert "Dangerous root recursive file deletion" in content_text


def test_mcp_unknown_tool_flagged_not_blocked():
    """未知のツール名に対しても危険操作時は遮断せず通知すること"""
    server = LocalMCPServer()
    req = {
        "jsonrpc": "2.0",
        "id": 12,
        "method": "tools/call",
        "params": {
            "name": "run_command",
            "arguments": {
                "CommandLine": "rm -rf /"
            }
        }
    }
    resp = server.handle_request_dict(req)
    assert "error" not in resp
    assert "result" in resp
    content_text = resp["result"]["content"][0]["text"]
    assert "AEGIS AUDIT WARNING" in content_text
    assert "NOT blocked" in content_text


def test_universal_notifier_layers(tmp_path):
    """UniversalNotifier の各通知レイヤー（STDERR, ログファイル, インバンド文字列）の検証"""
    alert_log = tmp_path / "alerts.log"
    notifier = UniversalNotifier(alert_log_path=str(alert_log))
    judge = SentinelJudge()
    verdict = judge.evaluate_tool_call("run_command", {"CommandLine": "rm -rf /"})

    # STDERR キャプチャ用
    old_stderr = sys.stderr
    capture_stderr = io.StringIO()
    try:
        sys.stderr = capture_stderr
        inband_msg = notifier.notify_violation(
            tool_name="run_command",
            arguments={"CommandLine": "rm -rf /"},
            verdict=verdict
        )
    finally:
        sys.stderr = old_stderr

    # 1. STDERR 出力とターミナルベル (\a) の検証
    stderr_output = capture_stderr.getvalue()
    assert "[AEGIS AUDIT NOTICE]" in stderr_output
    assert "\a" in stderr_output
    assert "Execution NOT blocked" in stderr_output

    # 2. インバンド警告メッセージの検証
    assert "AEGIS AUDIT WARNING" in inband_msg
    assert "NOT blocked" in inband_msg

    # 3. アラートログファイルへの追記検証
    assert alert_log.exists()
    log_content = alert_log.read_text(encoding="utf-8")
    assert "run_command" in log_content
    assert "Dangerous root recursive file deletion" in log_content


def test_cloud_mcp_fallback():
    """存在しないクラウドエンドポイントへ接続した際の自動ローカルフォールバックテスト"""
    client = CloudMCPClient(
        endpoint="http://127.0.0.1:59999/non-existent-endpoint",
        timeout_sec=0.5,
        fallback_to_local=True
    )
    req = {
        "jsonrpc": "2.0",
        "id": 20,
        "method": "tools/call",
        "params": {
            "name": "aegis_inspect_action",
            "arguments": {
                "action_type": "run_command",
                "parameters": {"CommandLine": "git diff"}
            }
        }
    }
    # クラウド接続エラーが発生するが、自動でローカルへフォールバックして成功すること
    resp = client.dispatch(req)
    assert "result" in resp
    assert "PASSED" in resp["result"]["content"][0]["text"]
