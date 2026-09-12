"""
Recorder Module for Agent Aegis Harness
Handles 5W1H audit trail generation, Dual-Stream logging, and Antigravity hook integration
"""
from aegis.recorder.tracer import AegisRecorder
from aegis.recorder.antigravity_adapter import AntigravityAegisAdapter

__all__ = ["AegisRecorder", "AntigravityAegisAdapter"]
