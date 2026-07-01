from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from nova.node.continuity import append_receipt
from nova.node.ledger import runtime_dir, stable_hash, stable_json


def write_coding_receipt(
    *,
    trace_id: str,
    task: dict[str, Any],
    governance: dict[str, Any],
    result: dict[str, Any],
    tool: str,
) -> str:
    entry = {
        "entry_type": "nodeToolReceipt",
        "trace_id": trace_id,
        "timestamp": int(time.time()),
        "policy_version": governance.get("policy_version"),
        "decision": governance.get("decision"),
        "tool": tool,
        "intent": task.get("intent"),
        "caller_id": task.get("caller_id"),
        "file_path": task.get("file_path"),
        "instruction": task.get("instruction"),
        "current_code": task.get("current_code"),
        "goal": task.get("goal"),
        "model": task.get("model", "local"),
        "receipts": list(governance.get("receipts", [])) + list(result.get("receipts", [])),
        "input_snapshot": task,
        "output_snapshot": result,
        "input_hash": stable_hash(task),
        "output_hash": stable_hash(result),
        "original_code_hash": stable_hash(task.get("current_code", "")),
        "updated_code_preview": str(result.get("updated_code", ""))[:500],
        "glue_code_preview": str(result.get("glue_code", ""))[:500],
        "diff": result.get("diff", ""),
    }
    entry["receipt_hash"] = stable_hash(entry)
    path = _receipt_path(trace_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(entry) + "\n", encoding="utf-8")
    append_receipt(entry)
    return str(path.relative_to(runtime_dir()))


def _receipt_path(trace_id: str) -> Path:
    return runtime_dir() / "tool-receipts" / f"{trace_id}.json"
