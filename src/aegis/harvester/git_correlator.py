"""
Git Commit & Pull Request Multi-tier Correlator for AI Session Auditing
Correlates AI developer operations (prompts, edits, affected files) to Git commits and PRs
using temporal proximity, file overlap (Jaccard), and semantic token heuristics.
"""
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from aegis.models import GitCorrelationContext, NormalizedAIEvent


@dataclass
class GitCommitMetadata:
    commit_sha: str
    timestamp: datetime
    author: str
    message: str
    changed_files: List[str] = field(default_factory=list)
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None


class GitPRCorrelator:
    """Git コミットおよび PR と AI 監査イベントを高精度に紐付ける相関エンジン"""

    PR_REGEX_PATTERNS = [
        re.compile(r"Merge pull request #(\d+)", re.IGNORECASE),
        re.compile(r"\(#(\d+)\)"),
        re.compile(r"PR[\s-]?#?(\d+)", re.IGNORECASE),
        re.compile(r"pull/(\d+)", re.IGNORECASE),
    ]

    def __init__(self, repo_path: Path = Path(".")):
        self.repo_path = repo_path.resolve()
        self._commit_cache: Optional[List[GitCommitMetadata]] = None
        self._current_branch: Optional[str] = None

    def get_current_branch(self) -> str:
        """現在の Git ブランチ名を取得"""
        if self._current_branch:
            return self._current_branch
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode == 0:
                self._current_branch = res.stdout.strip()
                return self._current_branch
        except Exception:
            pass
        return "unknown"

    def load_recent_commits(self, max_commits: int = 200) -> List[GitCommitMetadata]:
        """Git 履歴からコミット情報（SHA、時刻、作者、メッセージ、変更ファイル）を取得"""
        if self._commit_cache is not None:
            return self._commit_cache

        commits: List[GitCommitMetadata] = []
        try:
            # git log: %H (SHA), %at (author timestamp epoch), %an (author name), %s (subject)
            res = subprocess.run(
                ["git", "log", f"-n{max_commits}", "--pretty=format:%H|%at|%an|%s"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                check=False
            )
            if res.returncode != 0 or not res.stdout:
                self._commit_cache = []
                return []

            lines = res.stdout.strip().split("\n")
            for line in lines:
                if not line.strip():
                    continue
                parts = line.strip().split("|", 3)
                if len(parts) < 4:
                    continue
                sha, epoch_str, author, msg = parts[0], parts[1], parts[2], parts[3]
                try:
                    dt = datetime.utcfromtimestamp(int(epoch_str))
                except Exception:
                    dt = datetime.utcnow()

                # PR 番号の抽出
                pr_num = self._extract_pr_number(msg)

                # コミットで変更されたファイルを取得
                changed_files = self._get_commit_files(sha)

                commits.append(
                    GitCommitMetadata(
                        commit_sha=sha,
                        timestamp=dt,
                        author=author,
                        message=msg,
                        changed_files=changed_files,
                        pr_number=pr_num,
                        pr_url=f"https://github.com/pull/{pr_num}" if pr_num else None
                    )
                )
        except Exception:
            pass

        self._commit_cache = commits
        return commits

    def _get_commit_files(self, commit_sha: str) -> List[str]:
        """単一コミットで変更されたファイル一覧を取得"""
        try:
            res = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_sha],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                check=False
            )
            if res.returncode == 0 and res.stdout:
                return [f.strip().replace("\\", "/") for f in res.stdout.strip().splitlines() if f.strip()]
        except Exception:
            pass
        return []

    def _extract_pr_number(self, message: str) -> Optional[int]:
        """コミットメッセージから PR 番号を検出"""
        for pattern in self.PR_REGEX_PATTERNS:
            match = pattern.search(message)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    pass
        return None

    def correlate_event(
        self,
        event: NormalizedAIEvent,
        commits: Optional[List[GitCommitMetadata]] = None
    ) -> GitCorrelationContext:
        """
        AI 監査イベントを最適な Git コミットに紐付ける。
        多層ハイブリッドスコアリング:
        - 時間近接度 (S_temporal)
        - ファイル重複度 (S_files)
        - 意図・メッセージ類似度 (S_semantic)
        """
        if commits is None:
            commits = self.load_recent_commits()

        branch = self.get_current_branch()

        if not commits:
            return GitCorrelationContext(
                branch_name=branch,
                confidence_score=0.0,
                confidence_level="UNLINKED"
            )

        best_commit: Optional[GitCommitMetadata] = None
        best_score = 0.0

        ai_files = self._normalize_file_paths(event.affected_files)
        ai_tokens = self._tokenize(event.trigger.sanitized_prompt)

        for c in commits:
            score = self._compute_score(event.timestamp, ai_files, ai_tokens, c)
            if score > best_score:
                best_score = score
                best_commit = c

        # 判定レベル
        if best_score >= 0.65:
            confidence_level = "HIGH"
        elif best_score >= 0.40:
            confidence_level = "MEDIUM"
        elif best_score >= 0.20:
            confidence_level = "LOW"
        else:
            confidence_level = "UNLINKED"

        if not best_commit or confidence_level == "UNLINKED":
            return GitCorrelationContext(
                branch_name=branch,
                confidence_score=round(best_score, 3),
                confidence_level="UNLINKED"
            )

        proof_str = (
            f"sha:{best_commit.commit_sha[:8]}|score:{best_score:.2f}|level:{confidence_level}"
            f"|pr:{best_commit.pr_number if best_commit.pr_number else 'none'}"
        )

        return GitCorrelationContext(
            commit_sha=best_commit.commit_sha,
            commit_timestamp=best_commit.timestamp,
            commit_author=best_commit.author,
            commit_message=best_commit.message,
            branch_name=branch,
            staged_files=best_commit.changed_files,
            pr_number=best_commit.pr_number,
            pr_url=best_commit.pr_url,
            confidence_score=round(best_score, 3),
            confidence_level=confidence_level,
            correlation_proof=proof_str
        )

    def _compute_score(
        self,
        event_time: datetime,
        ai_files: Set[str],
        ai_tokens: Set[str],
        commit: GitCommitMetadata
    ) -> float:
        """多層相関スコアを計算"""
        # 1. 時間近接度 (S_temporal)
        # コミットは通常 AI 操作の「直後」に行われる (commit_time >= event_time)
        delta_sec = (commit.timestamp - event_time).total_seconds()
        if 0 <= delta_sec <= 1800:       # 30分以内
            s_temp = 1.0
        elif 0 <= delta_sec <= 7200:     # 2時間以内
            s_temp = 0.8
        elif 0 <= delta_sec <= 28800:    # 8時間以内
            s_temp = 0.6
        elif 0 <= delta_sec <= 86400:    # 24時間以内
            s_temp = 0.4
        elif 0 <= delta_sec <= 604800:   # 7日以内
            s_temp = 0.2
        elif -3600 <= delta_sec < 0:     # 直前1時間のコミット (作業中の場合)
            s_temp = 0.3
        else:
            s_temp = 0.05

        # 2. ファイル重複度 (S_files)
        commit_files = self._normalize_file_paths(commit.changed_files)
        if ai_files and commit_files:
            intersection = ai_files.intersection(commit_files)
            union = ai_files.union(commit_files)
            s_files = len(intersection) / len(union) if union else 0.0
            # 1つでも完全一致していればボーナス
            if intersection:
                s_files = max(s_files, 0.7)
        else:
            s_files = 0.0

        # 3. 意図・コミットメッセージ類似度 (S_semantic)
        commit_tokens = self._tokenize(commit.message)
        if ai_tokens and commit_tokens:
            common = ai_tokens.intersection(commit_tokens)
            s_sem = len(common) / max(len(ai_tokens), len(commit_tokens))
        else:
            s_sem = 0.0

        # 総合重み付け
        if ai_files:
            total = (0.30 * s_temp) + (0.50 * s_files) + (0.20 * s_sem)
        else:
            total = (0.60 * s_temp) + (0.40 * s_sem)

        return min(max(total, 0.0), 1.0)

    def _normalize_file_paths(self, file_paths: List[str]) -> Set[str]:
        """ファイルパスを比較可能な形式（小文字・ファイル名および相対パス）へ正規化"""
        normalized = set()
        for p in file_paths:
            clean = p.replace("\\", "/").strip().lower()
            if not clean:
                continue
            # ファイル名単体
            normalized.add(Path(clean).name)
            # 末尾2セグメント
            parts = clean.split("/")
            if len(parts) >= 2:
                normalized.add(f"{parts[-2]}/{parts[-1]}")
        return normalized

    def _tokenize(self, text: str) -> Set[str]:
        """テキストを英数字トークンに分解"""
        words = re.findall(r"[A-Za-z0-9_\-\.]{3,}", text.lower())
        stopwords = {"this", "that", "with", "from", "have", "need", "test", "file", "make", "user"}
        return {w for w in words if w not in stopwords}
