"""Scorpion Bridge Organ — read-only Scorpion status; Jarvis bridge gap documented."""

# Mythic: Scorpion Bridge Organ
# Engineering: ScorpionBridgeBridge
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-SB-01"
ORGAN_VERSION = "scorpion_bridge_organ.v1"
_DEFAULT_CASE = "tri-demo-001"


def _jarvis_bridge_present(root: Path) -> bool:
    return (root / "src" / "scorpion_bridge.py").is_file()


def build_scorpion_bridge_status(*, root: Path | None = None) -> dict[str, Any]:
    """Bounded Scorpion drift snapshot; bridge module absent until implemented."""
    root = root or Path(__file__).resolve().parents[1]
    bridge_present = _jarvis_bridge_present(root)
    proof_dir = root / "docs" / "proof" / "scorpion"
    ledger = proof_dir / "scorpion_snapshot_index.jsonl"
    scorpion_status: dict[str, Any] = {}
    try:
        from scorpion.governance import status_summary

        scorpion_status = status_summary(
            case_id=_DEFAULT_CASE,
            proof_dir=proof_dir,
            ledger_path=ledger,
        )
    except Exception as exc:
        scorpion_status = {"error": str(exc)[:120], "claim_label": "asserted"}

    claim = str(scorpion_status.get("claim_label") or "asserted")
    summary = (
        f"bridge={'present' if bridge_present else 'missing'};"
        f"scorpion_claim={claim};case={_DEFAULT_CASE}"
    )[:128]
    return {
        "scorpion_bridge_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "jarvis_bridge_present": bridge_present,
        "scorpion_case_id": _DEFAULT_CASE,
        "scorpion_claim_label": claim,
        "scorpion_status": {
            k: scorpion_status[k]
            for k in ("mode", "safety_state", "snapshot_index_rows")
            if k in scorpion_status
        },
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
