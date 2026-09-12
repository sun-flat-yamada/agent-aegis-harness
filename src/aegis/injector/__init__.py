"""
Aegis Non-Destructive Instruction Injector Package
"""
from aegis.injector.engine import NonDestructiveInjector
from aegis.injector.templates import INJECTION_MARKER, TARGET_TOOL_DEFINITIONS

__all__ = ["NonDestructiveInjector", "INJECTION_MARKER", "TARGET_TOOL_DEFINITIONS"]
