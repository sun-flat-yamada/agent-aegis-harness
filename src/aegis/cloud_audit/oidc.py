"""
GitHub Actions Keyless OIDC ID Token Attestation Adapter
Fetches and cryptographically attests execution context without long-lived credentials.
"""
import base64
import hashlib
import json
import os
import urllib.request
import urllib.error
from typing import Dict, Optional, Tuple

from aegis.models import OIDCAttestationClaim

class OIDCAttestationAdapter:
    """GitHub Actions OIDC ID Token を取得・検証しクレームを抽出するアダプタ"""

    def __init__(self, env: Optional[Dict[str, str]] = None):
        self.env = env if env is not None else dict(os.environ)

    def fetch_token(
        self,
        audience: str = "aegis-audit",
        request_url: Optional[str] = None,
        request_token: Optional[str] = None,
        timeout_seconds: float = 2.0,
    ) -> Optional[str]:
        """GitHub Actions ランナー内部エンドポイントから OIDC JWT を取得"""
        url = request_url or self.env.get("ACTIONS_ID_TOKEN_REQUEST_URL")
        token = request_token or self.env.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")

        if not url or not token:
            return None

        # audience パラメータを URL に付加
        sep = "&" if "?" in url else "?"
        full_url = f"{url}{sep}audience={audience}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json; api-version=2.0",
            "Content-Type": "application/json",
            "User-Agent": "Agent-Aegis-Harness",
        }

        req = urllib.request.Request(full_url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data.get("value")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, Exception):
            return None
        return None

    def parse_jwt_claim(self, raw_jwt: str) -> Optional[OIDCAttestationClaim]:
        """JWT トークンからクレームをパースし、SHA-256 ダイジェストを算出"""
        if not raw_jwt or "." not in raw_jwt:
            return None

        parts = raw_jwt.split(".")
        if len(parts) < 2:
            return None

        payload_b64 = parts[1]
        # Base64 パディング補正
        padding_needed = (-len(payload_b64)) % 4
        payload_b64 += "=" * padding_needed

        try:
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            claims = json.loads(payload_bytes.decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return None

        # トークン本体の SHA-256 ダイジェスト算出（平文は保存しない）
        token_hash = hashlib.sha256(raw_jwt.encode("utf-8")).hexdigest()

        return OIDCAttestationClaim(
            iss=claims.get("iss", "https://token.actions.githubusercontent.com"),
            sub=claims.get("sub", ""),
            aud=str(claims.get("aud", "")),
            repository=claims.get("repository", ""),
            repository_owner=claims.get("repository_owner"),
            ref=claims.get("ref"),
            sha=claims.get("sha"),
            workflow=claims.get("workflow"),
            run_id=str(claims.get("run_id", "")),
            raw_token_sha256=token_hash,
        )

    def fetch_and_attest(
        self,
        audience: str = "aegis-audit",
        request_url: Optional[str] = None,
        request_token: Optional[str] = None,
    ) -> Optional[OIDCAttestationClaim]:
        """OIDC トークンを取得してクレーム検証済みモデルを返却。平文トークンは即消去"""
        raw_jwt = self.fetch_token(
            audience=audience,
            request_url=request_url,
            request_token=request_token,
        )
        if not raw_jwt:
            return None

        claim = self.parse_jwt_claim(raw_jwt)
        # 平文トークンのメモリ破棄
        del raw_jwt
        return claim
