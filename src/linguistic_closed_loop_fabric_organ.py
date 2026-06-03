"""Linguistic Closed Loop Fabric Subsystem — Wave 14 attested anticipate→react loop."""

# Mythic: Linguistic Closed Loop Fabric Organ
# Engineering: LinguisticClosedLoopFabricEngine
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-CLF-01"
ORGAN_VERSION = "linguistic_closed_loop_fabric_organ.v1"


def build_linguistic_closed_loop_fabric_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    reg_path = root / "governance" / "meta_linguistic_registry.v1.json"
    reg: dict[str, Any] = {}
    if reg_path.is_file():
        reg = json.loads(reg_path.read_text(encoding="utf-8"))

    has_cycle = bool(reg.get("last_cycle_report"))
    has_predictive = bool(reg.get("last_predictive_cycle_report"))
    has_calibration = bool(reg.get("last_calibration_at"))
    has_queue = bool(reg.get("last_governance_queue"))
    has_full_cycle = bool(reg.get("last_full_cycle_report"))

    predictive_engine = (
        root / "src" / "governance_organs" / "linguistic_predictive_governance_engine.py"
    ).is_file()
    cycle_engine = (
        root / "src" / "governance_organs" / "linguistic_governance_cycle_engine.py"
    ).is_file()
    calibration_engine = (
        root / "src" / "governance_organs" / "linguistic_forecast_calibration_engine.py"
    ).is_file()
    queue_engine = (
        root / "src" / "governance_organs" / "linguistic_governance_queue_engine.py"
    ).is_file()

    closed_loop_ready = (
        predictive_engine
        and cycle_engine
        and calibration_engine
        and queue_engine
        and has_cycle
        and has_predictive
        and has_calibration
        and has_queue
        and has_full_cycle
    )

    closed_loop_score = 0
    att_path = reg.get("last_attestation_report")
    if att_path:
        full = root / att_path
        if full.is_file():
            att = json.loads(full.read_text(encoding="utf-8"))
            closed_loop_score = int(att.get("closed_loop_score", 0))

    return {
        "linguistic_closed_loop_fabric_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": (
            f"predictive={int(has_predictive)};cycle={int(has_cycle)};"
            f"calibration={int(has_calibration)};queue={int(has_queue)};"
            f"full={int(has_full_cycle)};score={closed_loop_score}"
        )[:128],
        "last_predictive_cycle_in_registry": has_predictive,
        "last_governance_cycle_in_registry": has_cycle,
        "last_calibration_in_registry": has_calibration,
        "last_governance_queue_in_registry": has_queue,
        "last_full_cycle_in_registry": has_full_cycle,
        "closed_loop_ready": closed_loop_ready,
        "closed_loop_score": closed_loop_score,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
