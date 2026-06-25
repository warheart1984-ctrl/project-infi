"""UGR deliberation trace viewer — read-only JSONL trace access."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _runtime_traces_path(runtime: Any | None = None) -> Path:
    if runtime is not None and hasattr(runtime, "traces_path"):
        return Path(runtime.traces_path)
    configured = os.getenv("AAIS_RUNTIME_DIR")
    root = Path(configured).expanduser() if configured else Path(__file__).resolve().parents[3] / ".runtime"
    return root / "ugr" / "traces.jsonl"


def _summarize_trace(row: dict[str, Any]) -> dict[str, Any]:
    rail = dict(row.get("rail_decision") or {})
    return {
        "trace_id": row.get("trace_id"),
        "status": row.get("status"),
        "intent": row.get("intent"),
        "tenant_id": row.get("tenant_id"),
        "lane_count": row.get("lane_count"),
        "accepted_beliefs": row.get("accepted_beliefs"),
        "rail": rail.get("rail"),
        "risk": rail.get("risk"),
        "rail_rationale": rail.get("rationale"),
    }


def _wrap_readout(payload: dict[str, Any]) -> dict[str, Any]:
    from src.aais_ul.runtime import attach_ul_substrate

    return attach_ul_substrate(dict(payload))


def load_deliberation_traces(
    *,
    runtime: Any | None = None,
    limit: int = 20,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Load recent UGR deliberation traces from JSONL."""
    path = _runtime_traces_path(runtime)
    if not path.exists():
        return _wrap_readout(
            {
            "status": "empty",
            "traces_path": str(path),
            "trace_count": 0,
            "traces": [],
            "runtime_effect": "readout_only",
            }
        )

    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    if trace_id:
        needle = str(trace_id).strip()
        matches = [row for row in rows if str(row.get("trace_id") or "") == needle]
        return _wrap_readout(
            {
            "status": "ok" if matches else "not_found",
            "traces_path": str(path),
            "trace_count": len(matches),
            "traces": matches,
            "summaries": [_summarize_trace(row) for row in matches],
            "runtime_effect": "readout_only",
            }
        )

    selected = rows[-max(1, int(limit or 20)) :]
    selected.reverse()
    return _wrap_readout(
        {
        "status": "ok",
        "traces_path": str(path),
        "trace_count": len(rows),
        "returned": len(selected),
        "summaries": [_summarize_trace(row) for row in selected],
        "traces": selected,
        "runtime_effect": "readout_only",
        }
    )
