from __future__ import annotations

from typing import Any

from nova.node.tools.coder_tool import run as coder_run
from nova.node.tools.explain_tool import run as explain_run
from nova.node.tools.wiring_tool import run as wiring_run


class UnknownToolIntent(ValueError):
    pass


TOOLS = {
    "code": {
        "handler_name": "coder_run",
        "profile": "N2",
        "capabilities": ["patch", "refactor", "scaffold"],
        "tool_manifest_name": "coder_tool",
        "owner_agent": "agent-coder",
    },
    "wire": {
        "handler_name": "wiring_run",
        "profile": "N2",
        "capabilities": ["glue_code", "routes", "manifests", "config"],
        "tool_manifest_name": "wiring_tool",
        "owner_agent": "agent-wiring",
    },
    "explain": {
        "handler_name": "explain_run",
        "profile": "N2",
        "capabilities": ["patch_explanation", "risk_assessment", "test_recommendations"],
        "tool_manifest_name": "explain_tool",
        "owner_agent": "agent-coder",
    },
}


def invoke_tool(intent: str | None, task: dict[str, Any]) -> dict[str, Any]:
    tool_entry = TOOLS.get(str(intent or ""))
    if not tool_entry:
        raise UnknownToolIntent(str(intent or ""))
    handler = globals()[str(tool_entry["handler_name"])]
    return handler(task)
