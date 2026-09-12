"""
Aegis MCP Security Gateway Package
"""
from aegis.mcp_gateway.protocol import MCP_TOOLS_MANIFEST
from aegis.mcp_gateway.server import LocalMCPServer
from aegis.mcp_gateway.client import CloudMCPClient

__all__ = ["MCP_TOOLS_MANIFEST", "LocalMCPServer", "CloudMCPClient"]
