from __future__ import annotations

import difflib
import json
from typing import Any

from nova.node.ledger import runtime_dir
from nova.node.policy import GovernanceRuntime
from nova.node.tools.local_model import generate


def load_receipt(trace_id: str) -> dict[str, Any]:
    path = runtime_dir() / "tool-receipts" / f"{trace_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Receipt not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def replay_coding(trace_id: str) -> dict[str, Any]:
    receipt = load_receipt(trace_id)
    task = {
        "intent": receipt.get("intent"),
        "file_path": receipt.get("file_path"),
        "instruction": receipt.get("instruction"),
        "current_code": receipt.get("current_code") or "",
    }
    governance = GovernanceRuntime().enforce_invariants(task)
    updated_code = generate(_coding_prompt(task), model="qwen2.5-coder:3b", temperature=0.15)
    original_preview = str(receipt.get("updated_code_preview") or "")
    deterministic = updated_code.strip().startswith(original_preview.strip())
    diff_lines = difflib.unified_diff(
        original_preview.splitlines(),
        updated_code.splitlines(),
        lineterm="",
    )
    return {
        "trace_id": trace_id,
        "intent": receipt.get("intent"),
        "policy_version": receipt.get("policy_version") or governance.get("policy_version"),
        "deterministic": deterministic,
        "diff_against_original": "\n".join(diff_lines),
    }


def _coding_prompt(task: dict[str, Any]) -> str:
    return f"""
You are a constitutional coding tool.
Apply the following instruction to the provided code.

Instruction:
{task.get('instruction') or ''}

Current Code:
{task.get('current_code') or ''}

Return ONLY the updated code.
"""
