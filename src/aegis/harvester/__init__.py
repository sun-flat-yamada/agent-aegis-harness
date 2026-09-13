"""
Aegis Harvester Package
"""
from aegis.harvester.claude import ClaudeSessionParser
from aegis.harvester.copilot_parser import CopilotDeltaSessionParser
from aegis.harvester.discoverer import DiscoveryTarget, LocalStorageDiscoverer
from aegis.harvester.git_correlator import GitPRCorrelator
from aegis.harvester.retro_auditor import RetroAuditReport, RetroactiveSessionAuditor
from aegis.harvester.watcher import SessionHarvester

__all__ = [
    "ClaudeSessionParser",
    "CopilotDeltaSessionParser",
    "DiscoveryTarget",
    "GitPRCorrelator",
    "LocalStorageDiscoverer",
    "RetroAuditReport",
    "RetroactiveSessionAuditor",
    "SessionHarvester",
]

