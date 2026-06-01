"""workflow_definition.v1"""

from __future__ import annotations

from typing import Any

from platform.common import new_id

WORKFLOW_VERSION = "platform.workflow_definition.v1"


def build_workflow(
    *,
    org_id: str,
    name: str,
    steps: list[dict[str, str]],
    workflow_id: str | None = None,
) -> dict[str, Any]:
    return {
        "workflow_version": WORKFLOW_VERSION,
        "workflow_id": workflow_id or new_id("wf"),
        "org_id": org_id,
        "name": name,
        "steps": steps,
    }
