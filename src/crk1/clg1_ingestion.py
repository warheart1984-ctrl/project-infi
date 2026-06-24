"""Ingest CRR-1 wire receipts into CLG-1 as CalibrationEvent nodes."""

from __future__ import annotations

from typing import Any

from src.crk1.clg1_store import CLG1Store


class CLG1Ingestion:
    """
    Ingest CRR-1 receipts into CLG-1 as CalibrationEvent nodes
    and link them to stewards, decisions, and invariants.
    """

    def __init__(self, store: CLG1Store) -> None:
        self.store = store

    def ingest_crr1(self, crr1: dict[str, Any]) -> str:
        """
        Create a CalibrationEvent node and edges from a CRR-1.
        Returns the new CalibrationEvent ID.
        """
        event_id = self.store.create_node(
            kind="CalibrationEvent",
            props={
                "receipt_type": crr1["receipt_type"],
                "timestamp_utc": crr1["timestamp_utc"],
                "steward_id": crr1["steward_id"],
                "crr_id": crr1.get("crr_id"),
                "expected_outcome": crr1["expected_outcome"],
                "observed_outcome": crr1["observed_outcome"],
                "contradiction_delta": crr1["contradiction_delta"],
                "surprise_magnitude": crr1["surprise_magnitude"],
                "calibration_change": crr1["calibration_change"],
                "calibration_delta": crr1.get("calibration_delta", crr1["calibration_change"]),
                "future_implications": crr1.get("future_implications", []),
                "reality_channel": crr1.get("reality_channel"),
            },
        )

        steward_id = str(crr1["steward_id"])
        steward_node = self.store.ensure_node(f"Steward:{steward_id}", "Steward", {"id": steward_id})
        self.store.create_edge(src=steward_node, dst=event_id, kind="PERFORMED_CALIBRATION")

        links = crr1.get("links", {}) or {}
        if links.get("decision_id"):
            decision_id = str(links["decision_id"])
            decision_node = self.store.ensure_node(
                f"Decision:{decision_id}",
                "Decision",
                {"id": decision_id},
            )
            self.store.create_edge(src=decision_node, dst=event_id, kind="CORRECTS_DECISION")

        if links.get("expectation_id"):
            expectation_id = str(links["expectation_id"])
            expectation_node = self.store.ensure_node(
                f"Expectation:{expectation_id}",
                "Expectation",
                {"id": expectation_id},
            )
            self.store.create_edge(src=expectation_node, dst=event_id, kind="CORRECTS_EXPECTATION")

        if links.get("evidence_id"):
            evidence_id = str(links["evidence_id"])
            evidence_node = self.store.ensure_node(
                f"Evidence:{evidence_id}",
                "Evidence",
                {"id": evidence_id},
            )
            self.store.create_edge(src=evidence_node, dst=event_id, kind="SUPPORTED_BY_EVIDENCE")

        return event_id
