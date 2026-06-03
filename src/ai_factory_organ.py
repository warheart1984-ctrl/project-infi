"""AI Factory Organ — read-only governed mind fabrication posture."""

# Mythic: Ai Factory Organ
# Engineering: AiFactoryEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-AFO-01"
ORGAN_VERSION = "ai_factory_organ.v1"


def build_ai_factory_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    runtime_root = root / ".runtime" / "ai_factory"
    receipt_present = False
    active_build_id = None
    ledger_count = 0
    try:
        from ai_factory.orchestrator import build_status

        snapshot = build_status(runtime_root=runtime_root)
        active_build_id = snapshot.get("active_build_id")
        ledger_entries = snapshot.get("ledger_entries") or []
        ledger_count = len(ledger_entries) if isinstance(ledger_entries, list) else 0
        if active_build_id:
            receipt_path = runtime_root / str(active_build_id) / "AI_BUILD_RECEIPT.json"
            receipt_present = receipt_path.is_file()
    except Exception:
        pass

    summary = (
        f"active={active_build_id or 'none'};"
        f"receipt={int(receipt_present)};"
        f"ledger={ledger_count};read_only=1"
    )[:128]
    return {
        "ai_factory_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "factory_id": "ai_factory.v1",
        "runtime_root": str(runtime_root),
        "active_build_id": active_build_id,
        "build_receipt_present": receipt_present,
        "ledger_entry_count": ledger_count,
        "deploy_authority_via_organ": False,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
