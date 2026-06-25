"""Read-only Jarvis bridge to Scorpion governance surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any

BRIDGE_VERSION = "scorpion_bridge.v1"
DEFAULT_CASE = "tri-demo-001"


def bridge_status(*, root: Path | None = None, case_id: str = DEFAULT_CASE) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    proof_dir = root / "docs" / "proof" / "scorpion"
    ledger = proof_dir / "scorpion_snapshot_index.jsonl"
    scorpion_status: dict[str, Any]
    try:
        from scorpion.governance import status_summary

        scorpion_status = status_summary(
            case_id=case_id,
            proof_dir=proof_dir,
            ledger_path=ledger,
        )
    except Exception as exc:
        scorpion_status = {"error": str(exc)[:200], "claim_label": "asserted"}

    return {
        "bridge_version": BRIDGE_VERSION,
        "read_only": True,
        "case_id": case_id,
        "proof_dir": str(proof_dir),
        "scorpion_status": scorpion_status,
        "claim_label": str(scorpion_status.get("claim_label") or "asserted"),
    }
