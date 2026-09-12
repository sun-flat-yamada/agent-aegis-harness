"""
Non-Destructive Pointer Injection Engine for Agent Aegis Harness
Appends a single pointer line to target AI configuration files without overwriting.
"""
from pathlib import Path
from typing import Dict, List, Optional

from aegis.injector.templates import INJECTION_MARKER, TARGET_TOOL_DEFINITIONS


class NonDestructiveInjector:
    """既存設定を一切破壊せず、末尾に 1 行の参照ポインタのみを安全に追加するエンジン"""

    def __init__(self, repo_path: Path = Path(".")):
        self.repo_path = repo_path

    def inject_all(self, selected_tools: Optional[List[str]] = None) -> Dict[str, str]:
        """指定された（またはすべての）AIツール定義ファイルに対して非破壊インジェクションを実行"""
        results = {}
        target_keys = selected_tools if selected_tools and "all" not in selected_tools else list(TARGET_TOOL_DEFINITIONS.keys())

        for tool_key in target_keys:
            if tool_key not in TARGET_TOOL_DEFINITIONS:
                continue
            spec = TARGET_TOOL_DEFINITIONS[tool_key]
            target_path = self.repo_path / spec["target_file"]
            status = self.inject_single(target_path, spec["pointer"])
            results[tool_key] = status

        return results

    def inject_single(self, target_path: Path, pointer_text: str) -> str:
        """単一のファイルに対する非破壊追記（冪等性を保証）"""
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if target_path.exists():
            content = target_path.read_text(encoding="utf-8")
            if INJECTION_MARKER in content:
                return "SKIPPED_ALREADY_INJECTED"

            # 既存ファイルの末尾に改行を付与して安全に追記
            separator = "\n" if not content.endswith("\n") else ""
            target_path.write_text(content + separator + "\n" + pointer_text, encoding="utf-8")
            return "APPENDED"
        else:
            # ファイルが存在しない場合はポインタ行のみを安全に新規作成
            target_path.write_text(pointer_text, encoding="utf-8")
            return "CREATED_NEW"
