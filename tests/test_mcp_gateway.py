"""
Tests for Aegis MCP Security Gateway (Local and Cloud Fallback)
"""
import pytest
from aegis.mcp_gateway.server import LocalMCPServer
from aegis.mcp_gateway.client import CloudMCPClient


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


def test_mcp_inspect_action_blocked():
    """危険なコマンドの即時ブロックテスト"""
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
    assert "error" in resp
    assert resp["error"]["code"] == -32000
    assert "BLOCKED" in resp["error"]["message"]


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
