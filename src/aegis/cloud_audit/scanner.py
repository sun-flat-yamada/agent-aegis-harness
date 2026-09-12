"""
Git Pull Request Diff Scanner & Protected Files Checker for CI
Inspects code changes for sensitive credentials, protected file alterations, and context drift.
"""
import subprocess
from pathlib import Path
from typing import List, Optional, Set
from pydantic import BaseModel, Field

from aegis.models import ViolationRecord, ViolationSeverity
from aegis.sentinel.redactor import SensitiveRedactor

DEFAULT_PROTECTED_PATTERNS = [
    ".github/workflows/",
    ".aegis/rules/",
    ".aegis/schemas/",
    ".aegis/config.yaml",
]

class DiffScanResult(BaseModel):
    """PR 差分スキャン結果モデル"""
    is_clean: bool = True
    violations: List[ViolationRecord] = Field(default_factory=list)
    masked_findings: List[str] = Field(default_factory=list)
    files_scanned: List[str] = Field(default_factory=list)
    diff_stat: str = ""

class CloudDiffScanner:
    """PR の差分内容および変更対象ファイルを走査・検閲するスキャナー"""

    def __init__(
        self,
        repo_path: Optional[Path] = None,
        protected_patterns: Optional[List[str]] = None,
        redactor: Optional[SensitiveRedactor] = None,
    ):
        self.repo_path = repo_path or Path.cwd()
        self.protected_patterns = protected_patterns or DEFAULT_PROTECTED_PATTERNS
        self.redactor = redactor or SensitiveRedactor()

    def scan_text(
        self,
        diff_text: str,
        modified_files: Optional[List[str]] = None,
        diff_stat: str = "",
    ) -> DiffScanResult:
        """メモリ上の差分テキストおよびファイル一覧を静的検査"""
        violations: List[ViolationRecord] = []
        files = modified_files or []
        
        # 1. 機密情報 / PII / API トークンの検査
        sanitized_text, applied = self.redactor.redact_text(diff_text)
        if applied:
            violations.append(
                ViolationRecord(
                    rule_id="RULE-CLOUD-SECRET-LEAK",
                    severity=ViolationSeverity.CRITICAL,
                    message=f"Credential or secret pattern detected in PR diff: {', '.join(applied)}",
                )
            )

        # 2. 保護対象ファイルの変更検査
        protected_mods = []
        for f in files:
            norm_f = f.replace("\\", "/")
            for pattern in self.protected_patterns:
                if pattern in norm_f or norm_f.startswith(pattern):
                    protected_mods.append(f)
                    break

        if protected_mods:
            violations.append(
                ViolationRecord(
                    rule_id="RULE-CLOUD-PROTECTED-FILE",
                    severity=ViolationSeverity.MEDIUM,
                    message=f"Protected repository configuration modified in PR: {', '.join(protected_mods)}",
                )
            )

        is_clean = len(violations) == 0
        return DiffScanResult(
            is_clean=is_clean,
            violations=violations,
            masked_findings=applied,
            files_scanned=files,
            diff_stat=diff_stat,
        )

    def scan_pr_diff(
        self,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
    ) -> DiffScanResult:
        """Git リポジトリから実際の PR 差分を取得して走査"""
        diff_text = ""
        diff_files: List[str] = []
        diff_stat = ""

        candidates = []
        if base_ref:
            target_base = f"origin/{base_ref}"
            target_head = head_ref or "HEAD"
            candidates.append(f"git diff {target_base}...{target_head}")
            candidates.append(f"git diff {base_ref}...{target_head}")

        candidates.extend([
            "git diff --cached",
            "git diff HEAD~1",
            "git diff",
        ])

        for cmd in candidates:
            try:
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=10,
                )
                if proc.returncode == 0 and proc.stdout:
                    diff_text = proc.stdout
                    # ファイル一覧取得
                    name_cmd = cmd.replace("git diff", "git diff --name-only")
                    name_proc = subprocess.run(
                        name_cmd,
                        shell=True,
                        cwd=str(self.repo_path),
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=5,
                    )
                    if name_proc.returncode == 0:
                        diff_files = [line.strip() for line in name_proc.stdout.splitlines() if line.strip()]
                    
                    # 統計情報取得
                    stat_cmd = cmd.replace("git diff", "git diff --stat")
                    stat_proc = subprocess.run(
                        stat_cmd,
                        shell=True,
                        cwd=str(self.repo_path),
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=5,
                    )
                    if stat_proc.returncode == 0:
                        diff_stat = stat_proc.stdout.strip()
                    break
            except Exception:
                continue

        return self.scan_text(
            diff_text=diff_text,
            modified_files=diff_files,
            diff_stat=diff_stat,
        )
