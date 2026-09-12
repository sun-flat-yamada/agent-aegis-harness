"""
Tests for Git Commit Correlator
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from aegis.recorder.git_correlator import GitCorrelator


def test_git_pre_commit_secret_blocking():
    """ステージング差分にシークレットがある場合に exit 1 でブロックすることを検証"""
    correlator = GitCorrelator()

    diff_with_secret = """
diff --git a/.env b/.env
+OPENAI_API_KEY=sk-proj-abc1234567890abcdef1234567890abcdef1234567890
"""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=diff_with_secret)
        exit_code = correlator.run_pre_commit()
        assert exit_code == 1


def test_git_pre_commit_clean_pass():
    """通常の安全な差分であれば通過 (exit 0) することを検証"""
    correlator = GitCorrelator()

    clean_diff = """
diff --git a/main.py b/main.py
+def hello():
+    print("Hello, world!")
"""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=clean_diff)
        exit_code = correlator.run_pre_commit()
        assert exit_code == 0
