"""
Cloud Workflow & Remote Agent Audit Package for Agent Aegis Harness
"""
from aegis.cloud_audit.detector import CloudContextDetector
from aegis.cloud_audit.oidc import OIDCAttestationAdapter
from aegis.cloud_audit.scanner import CloudDiffScanner, DiffScanResult
from aegis.cloud_audit.gate import CloudSentinelGate, CloudSentinelVerdict

__all__ = [
    "CloudContextDetector",
    "OIDCAttestationAdapter",
    "CloudDiffScanner",
    "DiffScanResult",
    "CloudSentinelGate",
    "CloudSentinelVerdict",
]
