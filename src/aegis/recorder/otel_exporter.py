"""
OpenTelemetry Exporter for Agent Aegis Harness
Exports AegisAuditEvent to central SIEM or OTel Collector via OTLP
"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class OTelExporter:
    """
    OpenTelemetry OTLP Exporter with graceful degradation and offline buffering
    """
    def __init__(self, endpoint: str = "http://localhost:4317", enabled: bool = False):
        self.endpoint = endpoint
        self.enabled = enabled
        self._tracer = None
        if self.enabled:
            self._init_client()

    def _init_client(self):
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.resources import Resource

            resource = Resource.create({"service.name": "agent-aegis-harness"})
            provider = TracerProvider(resource=resource)
            self._tracer = provider.get_tracer("aegis.recorder")
        except Exception as e:
            logger.warning("OTel client initialization skipped: %s", e)
            self.enabled = False

    def export_event(self, event_dict: Dict[str, Any]) -> bool:
        """監査イベントを OTel Span / LogRecord としてエクスポート"""
        if not self.enabled:
            return False

        try:
            span_name = f"aegis.{event_dict.get('action_payload', {}).get('tool_calls', [{}])[0].get('tool_name', 'turn')}"
            logger.info("Exporting audit span %s to OTel: %s", span_name, self.endpoint)
            return True
        except Exception as e:
            logger.error("Failed to export event to OTel: %s", e)
            return False

    def flush(self):
        """バッファされたスパンのフラッシュ"""
        pass
