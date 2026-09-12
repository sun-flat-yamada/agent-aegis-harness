"""
Tests for Non-Destructive Pointer Injector
"""
import pytest
from pathlib import Path
from aegis.injector.engine import NonDestructiveInjector
from aegis.injector.templates import INJECTION_MARKER


def test_non_destructive_append(tmp_path: Path):
    """既存のカスタム設定を破壊せず、末尾にのみポインタが追記されることを検証"""
    claude_md = tmp_path / "CLAUDE.md"
    original_content = "# Project Custom Instructions\n- Do not touch legacy code\n- Use tabs\n"
    claude_md.write_text(original_content, encoding="utf-8")

    injector = NonDestructiveInjector(repo_path=tmp_path)
    res = injector.inject_single(claude_md, f"{INJECTION_MARKER}\n@.aegis/instructions/aegis-claude-rules.md\n")

    assert res == "APPENDED"
    updated_content = claude_md.read_text(encoding="utf-8")
    # 元の内容が先頭に完全保持されていること
    assert updated_content.startswith(original_content)
    # マーカーが含まれていること
    assert INJECTION_MARKER in updated_content
    assert "@.aegis/instructions/aegis-claude-rules.md" in updated_content


def test_injector_idempotency(tmp_path: Path):
    """複数回実行しても二重追記されず、スキップされることを検証"""
    copilot_file = tmp_path / ".github" / "copilot-instructions.md"
    injector = NonDestructiveInjector(repo_path=tmp_path)

    # 1 回目の実行 (新規作成)
    res1 = injector.inject_single(copilot_file, f"{INJECTION_MARKER}\nFollow rules\n")
    assert res1 == "CREATED_NEW"
    content_after_first = copilot_file.read_text(encoding="utf-8")

    # 2 回目の実行 (スキップ)
    res2 = injector.inject_single(copilot_file, f"{INJECTION_MARKER}\nFollow rules\n")
    assert res2 == "SKIPPED_ALREADY_INJECTED"
    content_after_second = copilot_file.read_text(encoding="utf-8")

    # ファイル内容が一切増えていないこと
    assert content_after_first == content_after_second


def test_inject_all_tools(tmp_path: Path):
    """全ツールへの一括インジェクションが正常に動作することを検証"""
    injector = NonDestructiveInjector(repo_path=tmp_path)
    results = injector.inject_all()

    assert "claude" in results
    assert "copilot" in results
    assert "amazon_q" in results
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / ".github" / "copilot-instructions.md").exists()
    assert (tmp_path / ".amazonq" / "rules.md").exists()
