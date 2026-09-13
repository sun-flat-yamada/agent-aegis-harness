"""
Local AI Assistant Storage Discoverer
Detects and maps cached session files across VS Code (GitHub Copilot), Claude Code, and Cursor
based on workspace URIs and local application data paths.
"""
import json
import os
import sys
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DiscoveryTarget:
    client_tool: str
    file_path: Path
    workspace_uri: Optional[str] = None
    is_matched_workspace: bool = False
    last_modified: Optional[datetime] = None
    size_bytes: int = 0


class LocalStorageDiscoverer:
    """開発環境のローカルストレージから AI セッション履歴ファイルを自律探索するディスカバラー"""

    def __init__(self, target_repo_path: Optional[Path] = None):
        self.target_repo_path = (target_repo_path or Path(".")).resolve()

    def discover_all(self, tool_filter: str = "all") -> List[DiscoveryTarget]:
        """指定ツールフィルタ (all, copilot, claude, cursor) に応じてセッションファイルを探索"""
        targets: List[DiscoveryTarget] = []

        if tool_filter in ("all", "copilot", "github-copilot"):
            targets.extend(self.discover_vscode_copilot_sessions())

        if tool_filter in ("all", "claude", "claude-code"):
            targets.extend(self.discover_claude_sessions())

        if tool_filter in ("all", "cursor"):
            targets.extend(self.discover_cursor_sessions())

        # 更新日時の新しい順にソート
        targets.sort(key=lambda t: t.last_modified or datetime.min, reverse=True)
        return targets

    def get_vscode_storage_dirs(self) -> List[Path]:
        """OS に応じた VS Code の workspaceStorage ディレクトリパス群を返却"""
        paths = []
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA")
            if appdata:
                paths.append(Path(appdata) / "Code" / "User" / "workspaceStorage")
                paths.append(Path(appdata) / "Code - Insiders" / "User" / "workspaceStorage")
        elif sys.platform == "darwin":
            home = Path.home()
            paths.append(home / "Library" / "Application Support" / "Code" / "User" / "workspaceStorage")
            paths.append(home / "Library" / "Application Support" / "Code - Insiders" / "User" / "workspaceStorage")
        else:
            home = Path.home()
            paths.append(home / ".config" / "Code" / "User" / "workspaceStorage")
            paths.append(home / ".config" / "Code - Insiders" / "User" / "workspaceStorage")
        return [p for p in paths if p.exists() and p.is_dir()]

    def discover_vscode_copilot_sessions(self) -> List[DiscoveryTarget]:
        """VS Code workspaceStorage 配下の Copilot chatSessions/*.jsonl を探索"""
        targets: List[DiscoveryTarget] = []
        storage_dirs = self.get_vscode_storage_dirs()

        for s_dir in storage_dirs:
            try:
                for ws_dir in s_dir.iterdir():
                    if not ws_dir.is_dir():
                        continue

                    # workspace.json の確認
                    ws_json = ws_dir / "workspace.json"
                    ws_uri = None
                    is_match = False
                    if ws_json.exists():
                        try:
                            data = json.loads(ws_json.read_text(encoding="utf-8", errors="ignore"))
                            ws_uri = data.get("folder") or data.get("workspace")
                            if ws_uri:
                                is_match = self._is_uri_matching_repo(ws_uri)
                        except Exception:
                            pass

                    # chatSessions/*.jsonl の探索
                    chat_sessions_dir = ws_dir / "chatSessions"
                    if chat_sessions_dir.exists() and chat_sessions_dir.is_dir():
                        for jf in chat_sessions_dir.glob("*.jsonl"):
                            try:
                                stat = jf.stat()
                                targets.append(
                                    DiscoveryTarget(
                                        client_tool="github-copilot",
                                        file_path=jf,
                                        workspace_uri=ws_uri,
                                        is_matched_workspace=is_match,
                                        last_modified=datetime.utcfromtimestamp(stat.st_mtime),
                                        size_bytes=stat.st_size
                                    )
                                )
                            except Exception:
                                pass
            except Exception:
                pass

        return targets

    def discover_claude_sessions(self) -> List[DiscoveryTarget]:
        """~/.claude/projects/ 配下の Claude Code セッションファイルを探索"""
        targets: List[DiscoveryTarget] = []
        claude_dir = Path.home() / ".claude" / "projects"
        if not claude_dir.exists():
            return targets

        repo_name = self.target_repo_path.name.lower()

        try:
            for jf in claude_dir.glob("**/sessions/*.jsonl"):
                try:
                    stat = jf.stat()
                    # パスにリポジトリ名が含まれるか照合
                    is_match = repo_name in str(jf).lower()
                    targets.append(
                        DiscoveryTarget(
                            client_tool="claude-code",
                            file_path=jf,
                            workspace_uri=str(self.target_repo_path),
                            is_matched_workspace=is_match,
                            last_modified=datetime.utcfromtimestamp(stat.st_mtime),
                            size_bytes=stat.st_size
                        )
                    )
                except Exception:
                    pass
        except Exception:
            pass

        return targets

    def discover_cursor_sessions(self) -> List[DiscoveryTarget]:
        """Cursor の workspaceStorage 配下のセッションファイルを探索"""
        targets: List[DiscoveryTarget] = []
        cursor_storage = None
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA")
            if appdata:
                cursor_storage = Path(appdata) / "Cursor" / "User" / "workspaceStorage"
        elif sys.platform == "darwin":
            cursor_storage = Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "workspaceStorage"
        else:
            cursor_storage = Path.home() / ".config" / "Cursor" / "User" / "workspaceStorage"

        if not cursor_storage or not cursor_storage.exists():
            return targets

        for ws_dir in cursor_storage.iterdir():
            if not ws_dir.is_dir():
                continue
            ws_json = ws_dir / "workspace.json"
            ws_uri = None
            is_match = False
            if ws_json.exists():
                try:
                    data = json.loads(ws_json.read_text(encoding="utf-8", errors="ignore"))
                    ws_uri = data.get("folder") or data.get("workspace")
                    if ws_uri:
                        is_match = self._is_uri_matching_repo(ws_uri)
                except Exception:
                    pass

            chat_sessions_dir = ws_dir / "chatSessions"
            if chat_sessions_dir.exists():
                for jf in chat_sessions_dir.glob("*.jsonl"):
                    try:
                        stat = jf.stat()
                        targets.append(
                            DiscoveryTarget(
                                client_tool="cursor",
                                file_path=jf,
                                workspace_uri=ws_uri,
                                is_matched_workspace=is_match,
                                last_modified=datetime.utcfromtimestamp(stat.st_mtime),
                                size_bytes=stat.st_size
                            )
                        )
                    except Exception:
                        pass

        return targets

    def _is_uri_matching_repo(self, workspace_uri: str) -> bool:
        """ワークスペース URI (file:// または vscode-remote://) が現在のリポジトリと一致するか判定"""
        try:
            decoded = urllib.parse.unquote(workspace_uri).lower().replace("\\", "/")
            repo_str = str(self.target_repo_path).lower().replace("\\", "/")
            repo_name = self.target_repo_path.name.lower()

            if repo_str in decoded or f"/{repo_name}" in decoded:
                return True
        except Exception:
            pass
        return False
