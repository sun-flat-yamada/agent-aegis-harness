"""
Retroactive AI Session Auditor & Ingestion Orchestrator
Discovers cached AI sessions across local IDE storages, parses delta streams,
correlates operations with Git commits/PRs, tags provenance metadata,
and ingests events into the unified Aegis WAL and cryptographic audit trail.
"""
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from aegis.archivist.integrity import HashChainManager
from aegis.harvester.claude import ClaudeSessionParser
from aegis.harvester.copilot_parser import CopilotDeltaSessionParser
from aegis.harvester.discoverer import DiscoveryTarget, LocalStorageDiscoverer
from aegis.harvester.git_correlator import GitPRCorrelator
from aegis.models import (
    AegisAuditEvent,
    AuditReproducibility,
    EnvironmentInfo,
    IntegrityProof,
    NormalizedAIEvent,
    SentinelVerdict,
    VerdictStatus,
)
from aegis.recorder.wal import SQLiteWALStore


@dataclass
class RetroAuditReport:
    discovered_files_count: int = 0
    matched_workspace_files_count: int = 0
    extracted_events_count: int = 0
    correlated_commits_count: int = 0
    linked_prs_count: int = 0
    ingested_wal_count: int = 0
    ingested_audit_trail_count: int = 0
    events: List[NormalizedAIEvent] = field(default_factory=list)


class RetroactiveSessionAuditor:
    """ローカル AI セッションの後追い監査・相関・集積を一貫して実行するオーケストレーター"""

    def __init__(self, repo_path: Path = Path(".")):
        self.repo_path = repo_path.resolve()
        self.discoverer = LocalStorageDiscoverer(target_repo_path=self.repo_path)
        self.copilot_parser = CopilotDeltaSessionParser()
        self.claude_parser = ClaudeSessionParser()
        self.git_correlator = GitPRCorrelator(repo_path=self.repo_path)
        self.wal = SQLiteWALStore()

    def run_audit(
        self,
        tool_filter: str = "all",
        matched_only: bool = False,
        since: Optional[datetime] = None,
        correlate_git: bool = True,
        ingest: bool = True,
        log_file_path: Optional[Path] = None
    ) -> RetroAuditReport:
        """
        後追い監査の全パイプライン（探索 -> 抽出 -> 相関 -> タグ付け -> 集積）を実行
        """
        report = RetroAuditReport()

        # 1. ローカルストレージ探索
        targets = self.discoverer.discover_all(tool_filter=tool_filter)
        report.discovered_files_count = len(targets)

        # ワークスペース一致フィルタ
        if matched_only:
            targets = [t for t in targets if t.is_matched_workspace]
        report.matched_workspace_files_count = len(targets)

        # 2. セッションファイルからのイベント抽出
        extracted_events: List[NormalizedAIEvent] = []
        for target in targets:
            evs = self._parse_target(target)
            for e in evs:
                if since and e.timestamp < since:
                    continue
                # 諸元メタデータ・タグの補強
                if target.is_matched_workspace:
                    e.tags.append("workspace:matched")
                if target.workspace_uri:
                    e.tags.append(f"uri:{Path(target.workspace_uri).name}")
                extracted_events.append(e)

        report.extracted_events_count = len(extracted_events)

        # 3. Git コミット & PR 相関
        if correlate_git and extracted_events:
            commits = self.git_correlator.load_recent_commits()
            for ev in extracted_events:
                git_ctx = self.git_correlator.correlate_event(ev, commits=commits)
                ev.git_context = git_ctx
                if git_ctx.confidence_level in ("HIGH", "MEDIUM"):
                    report.correlated_commits_count += 1
                    ev.tags.append(f"git:correlated_{git_ctx.confidence_level.lower()}")
                    if git_ctx.commit_sha:
                        ev.tags.append(f"commit:{git_ctx.commit_sha[:8]}")
                    if git_ctx.pr_number:
                        report.linked_prs_count += 1
                        ev.tags.append(f"pr:{git_ctx.pr_number}")
                else:
                    ev.tags.append("git:unlinked")

        report.events = extracted_events

        # 4. 集積 (WAL & Hash-Chain Audit Trail)
        if ingest and extracted_events:
            self._ingest_events(extracted_events, report, log_file_path=log_file_path)

        return report

    def _parse_target(self, target: DiscoveryTarget) -> List[NormalizedAIEvent]:
        """ターゲットファイルに応じたパーサーでイベントを抽出"""
        if target.client_tool in ("github-copilot", "cursor"):
            return self.copilot_parser.parse_session_file(target.file_path)
        elif target.client_tool == "claude-code":
            events = self.claude_parser.parse_session_file(target.file_path)
            # Claude イベントにプロベナンスと諸元タグを付与
            for e in events:
                e.extraction_method = "retro_local_discovery"
                e.tags.extend(["source:claude-code", "extraction:retroactive", f"session:{target.file_path.stem}"])
            return events
        return []

    def _ingest_events(
        self,
        events: List[NormalizedAIEvent],
        report: RetroAuditReport,
        log_file_path: Optional[Path] = None
    ):
        """
        抽出されたイベントを本来の収集と同じ形式で SQLite WAL および audit-trail.jsonl に集積
        """
        target_log = log_file_path or Path(".aegis/logs/audit-trail.jsonl")
        target_log.parent.mkdir(parents=True, exist_ok=True)

        for ev in events:
            # WAL へのエンキュー
            try:
                self.wal.append_event({
                    "trace_id": ev.trace_id,
                    "timestamp": ev.timestamp.isoformat(),
                    "tool_name": ev.client_tool.value,
                    "status": "RETRO_INGESTED",
                    "summary": ev.trigger.sanitized_prompt[:100],
                    "extraction_method": ev.extraction_method,
                    "tags": ev.tags,
                    "commit_sha": ev.git_context.commit_sha if ev.git_context else None
                })
                report.ingested_wal_count += 1
            except Exception:
                pass

            # ハッシュチェーン台帳 (audit-trail.jsonl) への完全性封印記録
            try:
                self._append_to_audit_trail(ev, target_log)
                report.ingested_audit_trail_count += 1
            except Exception:
                pass

    def _append_to_audit_trail(self, ev: NormalizedAIEvent, log_path: Path):
        """HashChainManager を利用して暗号学的に連鎖させた監査レコードを追記"""
        latest_hash = HashChainManager.GENESIS_HASH
        if log_path.exists() and log_path.stat().st_size > 0:
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        rec = json.loads(line)
                        if "integrity" in rec and "current_record_hash" in rec["integrity"]:
                            latest_hash = rec["integrity"]["current_record_hash"]
            except Exception:
                pass

        ev_dict = ev.model_dump(mode="json")
        ev_dict["timestamp"] = ev.timestamp.isoformat()

        # HashChainManager で署名・連鎖
        signed_dict = HashChainManager.sign_record(ev_dict, latest_hash)

        integrity = signed_dict.get("integrity", {})
        ev.previous_record_hash = integrity.get("previous_record_hash", latest_hash)
        ev.current_record_hash = integrity.get("current_record_hash", latest_hash)

        # 追記保存
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(signed_dict, ensure_ascii=False) + "\n")
