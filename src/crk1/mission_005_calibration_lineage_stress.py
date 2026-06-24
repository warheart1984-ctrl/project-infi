"""Mission #005 — Calibration Lineage Stress Test (multi-steward continuity)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.crk1.calibration_lineage_graph import CalibrationLineageGraphCLG1
from src.crk1.crr1_builder import build_crr1
from src.crk1.crr1_validator import validate_crr1
from src.crk1.lawful_llm_adapter import LawfulLLMAdapter


@dataclass
class Mission005CalibrationLineageReport:
    """Pass/fail report for calibration lineage stress test."""

    passed: bool
    crr_count: int
    calibration_event_count: int
    stewards: list[str]
    crr_ids: list[str] = field(default_factory=list)
    lineage: list[dict[str, Any]] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "crr_count": self.crr_count,
            "calibration_event_count": self.calibration_event_count,
            "stewards": list(self.stewards),
            "crr_ids": list(self.crr_ids),
            "lineage": list(self.lineage),
            "failures": list(self.failures),
        }


class _StewardModel:
    """Per-steward model returning a fixed prediction."""

    def __init__(self, outcome: float, confidence: float = 0.8) -> None:
        self.outcome = outcome
        self.confidence = confidence

    def __call__(self, prompt: str) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "confidence": self.confidence,
            "assumptions": [f"steward_model_{self.outcome}"],
        }


def run_mission_005_calibration_lineage_stress(
    *,
    observed_outcome: float = 0.3,
    drift_threshold: float = 10.0,
) -> Mission005CalibrationLineageReport:
    """
    Multi-steward calibration lineage stress test.

    Three stewards predict differently; reality contradicts each; all CRR-1s
    ingest into shared CLG-1; lineage must reconstruct all corrections.
    """
    clg = CalibrationLineageGraphCLG1()
    decision_cluster = "phenomenon:falling_object_2m"

    stewards = {
        "steward_llm": _StewardModel(1.0, 0.9),
        "steward_human": _StewardModel(0.8, 0.7),
        "steward_agent": _StewardModel(1.2, 0.85),
    }

    crr_ids: list[str] = []
    lineage: list[dict[str, Any]] = []
    failures: list[str] = []

    for steward_id, model in stewards.items():
        adapter = LawfulLLMAdapter(
            model,
            steward_id=steward_id,
            clg=clg,
            channel_id="physics.fall",
            decision_cluster_id=decision_cluster,
        )
        exp = adapter.predict("Predict fall time for 2m drop.")
        evidence = adapter.observe({"value": observed_outcome, "strength": 1.0})
        _correction, crr1 = adapter.correct(exp, evidence)

        if not validate_crr1(crr1):
            failures.append(f"{steward_id}: CRR-1 validation failed")

        crr_ids.append(str(crr1["crr_id"]))
        lineage.append(
            {
                "steward_id": steward_id,
                "expected_outcome": crr1["expected_outcome"],
                "observed_outcome": crr1["observed_outcome"],
                "contradiction_delta": crr1["contradiction_delta"],
                "calibration_delta": crr1["calibration_delta"],
                "crr_id": crr1["crr_id"],
            }
        )

    calibration_events = [
        node for node in clg.nodes.values() if node.node_type == "CalibrationEvent"
    ]

    if len(crr_ids) != 3:
        failures.append(f"expected 3 CRR-1 receipts, got {len(crr_ids)}")
    if len(calibration_events) != 3:
        failures.append(f"expected 3 CalibrationEvent nodes, got {len(calibration_events)}")

    reconstructed = reconstruct_lineage(clg)
    if len(reconstructed) != 3:
        failures.append(f"lineage reconstruction returned {len(reconstructed)}, expected 3")

    for entry in lineage:
        match = next((r for r in reconstructed if r["crr_id"] == entry["crr_id"]), None)
        if match is None:
            failures.append(f"missing lineage entry for {entry['crr_id']}")
        elif match["calibration_delta"] != entry["calibration_delta"]:
            failures.append(f"calibration delta not traceable for {entry['crr_id']}")

    total_drift = sum(abs(e["calibration_delta"]) for e in lineage)
    if total_drift > drift_threshold:
        failures.append(f"drift {total_drift} exceeds threshold {drift_threshold}")

    for steward_id in stewards:
        profile = clg.steward_calibration_profile(steward_id)
        if profile["event_count"] == 0:
            failures.append(f"{steward_id} insulated — no calibration events")

    return Mission005CalibrationLineageReport(
        passed=len(failures) == 0,
        crr_count=len(crr_ids),
        calibration_event_count=len(calibration_events),
        stewards=list(stewards.keys()),
        crr_ids=crr_ids,
        lineage=lineage,
        failures=failures,
    )


def reconstruct_lineage(clg: CalibrationLineageGraphCLG1) -> list[dict[str, Any]]:
    """Reconstruct all calibration events from CLG-1 metadata."""
    events = [
        node
        for node in clg.nodes.values()
        if node.node_type == "CalibrationEvent"
    ]
    return sorted(
        [
            {
                "event_id": node.id,
                "crr_id": node.metadata.get("crr_id", ""),
                "steward_id": node.metadata.get("steward_id", ""),
                "calibration_delta": node.metadata.get("calibration_delta", 0.0),
                "channel_id": node.metadata.get("channel_id", ""),
            }
            for node in events
        ],
        key=lambda item: item["event_id"],
    )
