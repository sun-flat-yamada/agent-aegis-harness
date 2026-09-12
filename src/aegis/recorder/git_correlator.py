"""
Git Commit Correlation Hook for Agent Aegis Harness
Binds Git commits cryptographically to recent AI developer interaction sessions.
"""
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from aegis.recorder.wal import SQLiteWALStore
from aegis.sentinel.redactor import SensitiveRedactor


class GitCorrelator:
    """Git コミットと直前の AI 開発セッションを暗号学的にバインドするフックモジュール"""

    def __init__(self, repo_path: Path = Path(".")):
        self.repo_path = repo_path
        self.wal = SQLiteWALStore()
        self.redactor = SensitiveRedactor()

    def run_pre_commit(self) -> int:
        """コミット前検査: ステージングされたコード差分のシークレットスキャン"""
        try:
            res = subprocess.run(["git", "diff", "--cached"], cwd=self.repo_path, capture_output=True, text=True)
            if res.returncode == 0 and res.stdout:
                sanitized, applied = self.redactor.redact_text(res.stdout)
                if applied:
                    print(f"[AEGIS PRE-COMMIT BLOCKED] Unmasked secret pattern detected in staged diff: {', '.join(applied)}")
                    return 1
        except Exception:
            pass
        return 0

    def run_post_commit(self) -> Optional[str]:
        """コミット後処理: 最新コミット SHA と直近 AI 監査ハッシュをバインド"""
        try:
            res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_path, capture_output=True, text=True)
            if res.returncode != 0:
                return None
            commit_sha = res.stdout.strip()

            # 最新の監査記録ダイジェストを取得 (SQLite WAL / Hash Chain)
            latest_hash = self.wal.get_latest_record_hash()
            if not latest_hash:
                # 監査ログがまだない場合はスキップ
                return None

            # Git Notes (refs/notes/aegis) に注記してコミットと AI 監査を永続バインド
            note_content = (
                f"X-Aegis-Audit-Digest: {latest_hash}\n"
                f"Correlation-Timestamp: {datetime.utcnow().isoformat()}Z\n"
            )
            subprocess.run(
                ["git", "notes", "--ref=aegis", "add", "-f", "-m", note_content, commit_sha],
                cwd=self.repo_path,
                capture_output=True
            )
            return latest_hash
        except Exception:
            return None
