"""
Tests for Aegis CLI commands
"""
import pytest
typer = pytest.importorskip("typer")
from typer.testing import CliRunner
from aegis.cli import app

runner = CliRunner()

def test_cli_version():
    """aah version コマンドの出力確認"""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Agent Aegis Harness" in result.stdout

def test_cli_check():
    """aah check コマンドの実行確認"""
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "Sentinel Instant Audit" in result.stdout

def test_cli_verify():
    """aah verify コマンドの実行確認"""
    result = runner.invoke(app, ["verify"])
    assert result.exit_code == 0
    assert "Cryptographic proof verified" in result.stdout or "GENESIS ready" in result.stdout

def test_cli_report(tmp_path):
    """aah report コマンドによる Markdown レポート出力確認"""
    report_file = tmp_path / "report.md"
    result = runner.invoke(app, ["report", "-o", str(report_file)])
    assert result.exit_code == 0
    assert report_file.exists()
    assert "Agent Aegis Governance Audit Report" in report_file.read_text(encoding="utf-8")

def test_cli_refine():
    """aah refine コマンドの実行確認"""
    result = runner.invoke(app, ["refine"])
    assert result.exit_code == 0
    assert "Running Aegis Refiner" in result.stdout

def test_cli_check_instruction_pointers():
    """aah check における AI Instruction Pointer Integrity の検証確認"""
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "Instruction Pointer Integrity" in result.stdout
    assert "instruction pointers" in result.stdout
