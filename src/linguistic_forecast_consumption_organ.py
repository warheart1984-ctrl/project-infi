"""Linguistic Forecast Consumption Subsystem — forecast-in-cycle bridge posture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LFC-01"
ORGAN_VERSION = "linguistic_forecast_consumption_organ.v1"


def build_linguistic_forecast_consumption_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    policy_path = root / "governance" / "linguistic_governance_cycle_policy.v1.json"
    use_forecast = False
    if policy_path.is_file():
        use_forecast = bool(
            json.loads(policy_path.read_text(encoding="utf-8")).get(
                "use_forecast_in_cycle", False
            )
        )
    forecast = (root / "governance" / "linguistic_drift_forecast.v1.json").is_file()
    forecast_consumed = None
    cycle_dir = root / "governance" / "linguistic_governance_cycles"
    if cycle_dir.is_dir():
        files = sorted(cycle_dir.glob("*.json"), reverse=True)
        if files:
            latest = json.loads(files[0].read_text(encoding="utf-8"))
            phases = latest.get("phases") or {}
            forecast_consumed = phases.get("forecast_consumed")
    return {
        "linguistic_forecast_consumption_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": (
            f"use_forecast={int(use_forecast)};report={int(forecast)};"
            f"consumed={forecast_consumed}"
        )[:128],
        "use_forecast_in_cycle": use_forecast,
        "drift_forecast_report_present": forecast,
        "last_forecast_consumed": forecast_consumed,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
