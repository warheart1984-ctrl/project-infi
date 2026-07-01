from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter

from nova.node.identity import NodeIdentity
from nova.node.ledger import runtime_dir
from nova.node.policy import GovernanceRuntime

router = APIRouter()


def get_policy_state(policy_path: str = "./policy.yaml") -> dict[str, Any]:
    current = _read_text(Path(policy_path))
    previous_path = runtime_dir() / "policy.previous.yaml"
    previous = _read_text(previous_path)
    identity = NodeIdentity.load(policy_path)
    runtime = GovernanceRuntime(policy_path)
    return {
        "policy_version": str(runtime.policy.get("version", "1.0")),
        "policy_hash": identity.policy_hash,
        "current_policy": current,
        "previous_policy": previous,
        "diff": diff_policy_text(previous, current),
    }


def diff_policy_text(previous: str, current: str) -> dict[str, list[str]]:
    previous_lines = previous.splitlines()
    current_lines = current.splitlines()
    removed = [line for line in previous_lines if line not in current_lines]
    added = [line for line in current_lines if line not in previous_lines]
    changed = [
        line for line in current_lines
        if ":" in line and line.split(":", 1)[0] in {old.split(":", 1)[0] for old in previous_lines if ":" in old}
        and line not in previous_lines
    ]
    return {"added": added, "removed": removed, "changed": changed}


@router.get("/node/policy")
async def policy() -> dict[str, Any]:
    return get_policy_state()


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
