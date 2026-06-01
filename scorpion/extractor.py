"""Sandboxed anomaly extraction."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any


def extract_anomaly_bundle(
    *,
    case_id: str,
    drifts: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    chamber = Path(tempfile.mkdtemp(prefix=f"scorpion-replay-{case_id}-"))
    bundle = {
        "case_id": case_id,
        "drift_count": len(drifts),
        "drifts": drifts,
        "events": events,
    }
    bundle_path = chamber / "anomaly_bundle.json"
    bundle_path.write_text(json.dumps(bundle, sort_keys=True, indent=2), encoding="utf-8")
    trace_copy = chamber / "trace_copy.ndjson"
    with trace_copy.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, sort_keys=True))
            handle.write("\n")
    return {
        "mode": "extract",
        "claim_label": "proven" if drifts else "asserted",
        "safety_state": "sandbox_only",
        "replay_chamber": str(chamber),
        "bundle_path": str(bundle_path),
        "trace_copy": str(trace_copy),
    }


def cleanup_chamber(chamber_path: str) -> None:
    target = Path(chamber_path).expanduser().resolve()
    if target.exists() and target.is_dir():
        shutil.rmtree(target, ignore_errors=True)
