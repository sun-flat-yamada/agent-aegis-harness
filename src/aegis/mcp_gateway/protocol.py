"""
Model Context Protocol (MCP) Protocol & Tool Specs for Aegis Security Gateway
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# MCP 公開ツール定義一覧
MCP_TOOLS_MANIFEST: List[Dict[str, Any]] = [
    {
        "name": "aegis_inspect_action",
        "description": "Pre-execution security inspection of planned bash commands or file modifications using Sentinel.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "enum": ["run_command", "write_file", "edit_file"],
                    "description": "The type of action to inspect"
                },
                "parameters": {
                    "type": "object",
                    "description": "The action parameters (e.g. {'CommandLine': 'npm test'})"
                }
            },
            "required": ["action_type", "parameters"]
        }
    },
    {
        "name": "aegis_record_intent",
        "description": "Record reasoning trace (Chain of Thought / Why) and task intent into Aegis audit trail.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "intent_summary": {
                    "type": "string",
                    "description": "Short explanation of the intent behind subsequent tool actions"
                },
                "affected_components": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of files or components targeted"
                }
            },
            "required": ["intent_summary"]
        }
    }
]


class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
