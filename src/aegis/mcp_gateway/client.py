"""
Cloud MCP Gateway Client with Automatic Local Fallback
Forwards MCP tool requests to enterprise cloud gateway or seamlessly degrades to local sentinel.
"""
import urllib.request
import urllib.error
import json
from typing import Any, Dict, Optional
from aegis.mcp_gateway.server import LocalMCPServer


class CloudMCPClient:
    """クラウド MCP ゲートウェイへの転送クライアント（自動ローカルフォールバック機構付き）"""

    def __init__(
        self,
        endpoint: str,
        auth_token: Optional[str] = None,
        timeout_sec: float = 5.0,
        fallback_to_local: bool = True,
        policy_dir: str = ".aegis/rules"
    ):
        self.endpoint = endpoint
        self.auth_token = auth_token
        self.timeout_sec = timeout_sec
        self.fallback_to_local = fallback_to_local
        self.local_fallback = LocalMCPServer(policy_dir=policy_dir)

    def dispatch(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """リクエストをクラウドへ送信し、障害時はローカルへ自動フォールバック"""
        try:
            return self._send_to_cloud(request_dict)
        except Exception:
            if not self.fallback_to_local:
                raise
            # 自動ローカルフォールバック
            return self.local_fallback.handle_request_dict(request_dict)

    def _send_to_cloud(self, req: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        data = json.dumps(req).encode("utf-8")
        http_req = urllib.request.Request(self.endpoint, data=data, headers=headers, method="POST")

        with urllib.request.urlopen(http_req, timeout=self.timeout_sec) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
