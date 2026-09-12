"""
Sensitive Redactor for Agent Aegis Harness
Masks API keys, tokens, credentials, and PII from prompts and payloads
"""
import re
from typing import Any, Dict, List, Tuple

class SensitiveRedactor:
    PATTERNS = [
        # OpenAI API keys
        ("openai_api_key", re.compile(r"sk-[A-Za-z0-9]{20,60}"), "[REDACTED_OPENAI_KEY]"),
        # GitHub tokens
        ("github_token", re.compile(r"gh[pousr]-[A-Za-z0-9_]{36,255}"), "[REDACTED_GITHUB_TOKEN]"),
        # AWS Access Key
        ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED_AWS_KEY]"),
        # Generic Secret / Token / Password assignments
        (
            "generic_credential",
            re.compile(r'(?i)(?:api_key|token|secret|password|passwd|bearer)\s*[:=]\s*["\']?([A-Za-z0-9_\-\.]{16,})["\']?'),
            "[REDACTED_CREDENTIAL]"
        ),
        # IPv4 Address
        ("ipv4_address", re.compile(r"\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"), "[REDACTED_IP]"),
        # Email address
        ("email_address", re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"), "[REDACTED_EMAIL]"),
    ]

    def redact_text(self, text: str) -> Tuple[str, List[str]]:
        """
        文字列から機密情報をマスキングし、置換されたルール名のリストを返す
        """
        if not text:
            return "", []

        applied_redactions: List[str] = []
        sanitized = text

        for name, pattern, replacement in self.PATTERNS:
            if pattern.search(sanitized):
                applied_redactions.append(name)
                # Generic Credential の場合はキャプチャグループ部分のみ置換
                if name == "generic_credential":
                    sanitized = pattern.sub(lambda m: m.group(0).replace(m.group(1), replacement), sanitized)
                else:
                    sanitized = pattern.sub(replacement, sanitized)

        return sanitized, applied_redactions

    def redact_dict(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        辞書構造（ツール引数など）を再帰的にサニタイズ
        """
        sanitized: Dict[str, Any] = {}
        all_applied: List[str] = []

        for key, value in data.items():
            if isinstance(value, str):
                redacted_val, applied = self.redact_text(value)
                sanitized[key] = redacted_val
                all_applied.extend(applied)
            elif isinstance(value, dict):
                redacted_sub, applied = self.redact_dict(value)
                sanitized[key] = redacted_sub
                all_applied.extend(applied)
            elif isinstance(value, list):
                redacted_list = []
                for item in value:
                    if isinstance(item, str):
                        r_item, applied = self.redact_text(item)
                        redacted_list.append(r_item)
                        all_applied.extend(applied)
                    elif isinstance(item, dict):
                        r_item, applied = self.redact_dict(item)
                        redacted_list.append(r_item)
                        all_applied.extend(applied)
                    else:
                        redacted_list.append(item)
                sanitized[key] = redacted_list
            else:
                sanitized[key] = value

        return sanitized, list(set(all_applied))
