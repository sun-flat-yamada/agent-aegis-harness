"""
Universal Multi-Platform Security Notifier for Aegis MCP Security Gateway
Dispatches multi-layer notifications across Windows, macOS, Linux,
and client environments (VS Code, Copilot CLI, Claude Code, Terminal, SSH).
"""
import os
import sys
import platform
import shutil
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from aegis.models import SentinelVerdict


class UniversalNotifier:
    """
    マルチプラットフォーム・マルチクライアント対応の汎用セキュリティ通知エンジン。
    MCP 監査ゲートウェイが危険操作を検出した際、ツール実行を即時遮断することなく、
    4 層（STDERR+ベル、インバンドテキスト、OS ネイティブ通知、永続化ログ）で開発者へ通知します。
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
        violations = [v.message for v in verdict.violations]
        rules = sorted(list({v.rule_id for v in verdict.violations}))

        # Layer 1: STDERR 出力 + Terminal Attention (ベル音 \a)
        self._emit_stderr_notice(tool_name, violations, rules)

        # Layer 3: OS ネイティブ・デスクトップ通知 (非同期・非ブロッキング)
        title = "⚠️ Aegis Security Warning"
        msg = f"Potential dangerous operation in tool '{tool_name}': {'; '.join(violations[:2])}"
        self._dispatch_async_os_notification(title, msg)

        # Layer 4: 永続化アラートファイルへの追記
        self._append_alert_log(tool_name, violations, rules, arguments)

        # Layer 2: インバンド警告メッセージ生成（エージェントへのレスポンス用）
        inband_msg = (
            f"⚠️ [AEGIS AUDIT WARNING] Dangerous operation detected by Aegis Sentinel:\n"
            f"- Tool: {tool_name}\n"
            f"- Policy Violations: {'; '.join(violations)}\n"
            f"- Rules: {', '.join(rules)}\n"
            f"Note: This operation was NOT blocked (Audit-only mode). "
            f"Audit event was recorded as FLAGGED and developer notification was dispatched."
        )
        return inband_msg

    def _emit_stderr_notice(self, tool_name: str, violations: List[str], rules: List[str]) -> None:
        """
        Layer 1: STDERR への ANSI カラー警告バナーとターミナルベル (\a) の出力。
        ※ STDOUT は JSON-RPC プロトコル専用のため一切汚染しません。
        """
        try:
            banner = (
                f"\n\033[1;33m[AEGIS AUDIT NOTICE]\033[0m \033[1;31m⚠️ Potential Dangerous Operation Detected!\033[0m\n"
                f"  Tool    : \033[1m{tool_name}\033[0m\n"
                f"  Policy  : {', '.join(rules)}\n"
                f"  Reason  : {'; '.join(violations)}\n"
                f"  Status  : \033[1;32mExecution NOT blocked (Audit-only mode)\033[0m\a\n"
            )
            sys.stderr.write(banner)
            sys.stderr.flush()
        except Exception:
            pass

    def _dispatch_async_os_notification(self, title: str, message: str) -> None:
        """OS ネイティブ通知を別スレッドで非同期起動（呼び出し元をブロックしない）"""
        thread = threading.Thread(
            target=self._trigger_os_notification,
            args=(title, message),
            daemon=True
        )
        thread.start()

    def _trigger_os_notification(self, title: str, message: str) -> None:
        """
        Layer 3: OS ネイティブのデスクトップ通知。
        Windows, macOS, Linux に対応。失敗時は安全にスキップ。
        """
        current_os = platform.system()
        try:
            if current_os == "Darwin":
                # macOS: osascript
                clean_title = title.replace('"', '\\"')
                clean_msg = message.replace('"', '\\"')
                subprocess.run(
                    ["osascript", "-e", f'display notification "{clean_msg}" with title "{clean_title}" sound name "Ping"'],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2
                )
            elif current_os == "Linux":
                # Linux: notify-send (GUI デスクトップ環境で存在する場合)
                if shutil.which("notify-send"):
                    subprocess.run(
                        ["notify-send", "-u", "critical", title, message],
                        check=False,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=2
                    )
            elif current_os == "Windows":
                # Windows: PowerShell によるバルーン / トースト通知
                clean_msg = message.replace('"', '`"')
                clean_title = title.replace('"', '`"')
                ps_script = (
                    f'[reflection.assembly]::loadwithpartialname("System.Windows.Forms") | Out-Null; '
                    f'$notify = New-Object System.Windows.Forms.NotifyIcon; '
                    f'$notify.Icon = [System.Drawing.SystemIcons]::Warning; '
                    f'$notify.Visible = $true; '
                    f'$notify.ShowBalloonTip(3000, "{clean_title}", "{clean_msg}", [System.Windows.Forms.ToolTipIcon]::Warning)'
                )
                subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=3
                )
        except Exception:
            pass

    def _append_alert_log(
        self,
        tool_name: str,
        violations: List[str],
        rules: List[str],
        args: Dict[str, Any]
    ) -> None:
        """
        Layer 4: 永続化アラートファイル (.aegis/alerts.log) への追記。
        """
        try:
            self.alert_log_path.parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().isoformat()
            log_line = (
                f"[{timestamp}] [WARNING] tool={tool_name} rules={','.join(rules)} "
                f"violations={';'.join(violations)} args={str(args)[:200]}\n"
            )
            with open(self.alert_log_path, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            pass
