"""Continuity Graph v2 — CalibrationEvent-first lineage with CLG-1 store backend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.crk1.calibration_lineage_graph import CalibrationLineageGraphCLG1, CLGNode
from src.crk1.calibration_objects import CalibrationEvent
from src.crk1.clg1_ingestion import CLG1Ingestion
from src.crk1.clg1_store import CLG1Store, InMemoryCLG1Store
from src.crk1.continuity_graph import ContinuityGraph, GraphEdge, GraphNode
from src.crk1.correction_object import CalibrationCorrectionReceipt
from src.crk1.crk1_wire_v01 import CRK1Envelope


@dataclass
class ContinuityGraphV2:
    """
    Continuity Graph v2:
      - CalibrationEvent as first-class nodes (CLG-1 store)
      - Links: Steward, Decision, Expectation, Evidence, Invariants
      - Legacy wire graph + CalibrationLineageGraphCLG1 for backward compatibility
    """

    store: CLG1Store = field(default_factory=InMemoryCLG1Store)
    wire_graph: ContinuityGraph = field(default_factory=ContinuityGraph)
    clg: CalibrationLineageGraphCLG1 = field(default_factory=CalibrationLineageGraphCLG1)
    calibration_events: dict[str, CalibrationEvent] = field(default_factory=dict)
    crr_index: dict[str, CalibrationCorrectionReceipt] = field(default_factory=dict)
    store_event_index: dict[str, str] = field(default_factory=dict)
    ingestion: CLG1Ingestion = field(init=False)

    def __post_init__(self) -> None:
        self.ingestion = CLG1Ingestion(self.store)

    # ---------------------------------------------------------
    # WRITE PATHS
    # ---------------------------------------------------------
    def record_calibration_event(self, crr1: dict[str, Any]) -> str:
        """Ingest CRR-1 wire receipt into CLG-1 and return CalibrationEvent ID."""
        event_id = self.ingestion.ingest_crr1(crr1)
        crr_id = str(crr1.get("crr_id", event_id))
        self.store_event_index[crr_id] = event_id
        return event_id

    def add_wire_object(self, obj: CRK1Envelope | dict[str, Any]) -> None:
        self.wire_graph.add_object(obj)

    def ingest_calibration(
        self,
        crr: CalibrationCorrectionReceipt,
        event: CalibrationEvent | None = None,
        **kwargs: Any,
    ) -> CalibrationEvent:
        """Legacy path — rich CRR model + embedded CLG-1 graph."""
        event = self.clg.ingest_crr(crr, event, **kwargs)
        self.calibration_events[event.id] = event
        self.crr_index[crr.id] = crr

        self.wire_graph.nodes[event.id] = GraphNode(
            id=event.id,
            type="Receipt",
            receipt_id=crr.id,
            label=f"CEV {event.id}",
        )
        self.wire_graph.nodes[crr.id] = GraphNode(
            id=crr.id,
            type="Receipt",
            receipt_id=crr.id,
            label=crr.id,
        )
        self.wire_graph.edges.append(
            GraphEdge(from_id=event.id, to_id=crr.id, relation_type="documented_by")
        )
        channel_id = f"channel:{event.channel_id}"
        if channel_id not in self.wire_graph.nodes:
            self.wire_graph.nodes[channel_id] = GraphNode(
                id=channel_id,
                type="Evidence",
                receipt_id=event.channel_id,
                label=event.channel_id,
            )
        self.wire_graph.edges.append(
            GraphEdge(from_id=event.id, to_id=channel_id, relation_type="supported_by")
        )
        return event

    # ---------------------------------------------------------
    # READ PATHS
    # ---------------------------------------------------------
    def get_steward_lineage(self, steward_id: str) -> list[dict[str, Any]]:
        """Return all CalibrationEvents for a steward, ordered by time."""
        events = self.store.query(
            """
            MATCH (s:Steward {id: $sid})-[:PERFORMED_CALIBRATION]->(e:CalibrationEvent)
            RETURN e ORDER BY e.timestamp_utc
            """,
            {"sid": steward_id},
        )
        return [e["e"] for e in events]

    def get_decision_corrections(self, decision_id: str) -> list[dict[str, Any]]:
        """Return all CalibrationEvents that corrected a given decision."""
        events = self.store.query(
            """
            MATCH (d:Decision {id: $did})-[:CORRECTS_DECISION]-(e:CalibrationEvent)
            RETURN e ORDER BY e.timestamp_utc
            """,
            {"did": decision_id},
        )
        return [e["e"] for e in events]

    def trace_invariant_lineage(self, invariant_id: str) -> list[CLGNode]:
        return self.clg.trace_invariant_lineage(invariant_id)

    def steward_calibration_profile(self, steward_id: str) -> dict[str, Any]:
        store_events = self.get_steward_lineage(steward_id)
        if store_events:
            deltas = [float(item.get("calibration_delta", 0.0)) for item in store_events]
            return {
                "steward_id": steward_id,
                "event_count": len(store_events),
                "calibration_delta_sum": sum(deltas),
                "density": len(store_events) / max(1, len(self.store.nodes)),
                "events": store_events,
            }
        return self.clg.steward_calibration_profile(steward_id)

    def drift_correction_ratio(self, *, drift_index: float = 0.0) -> dict[str, Any]:
        return self.clg.drift_correction_ratio(drift_index=drift_index)

    def collapse_precursors(
        self,
        authority_scores: dict[str, float],
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        return self.clg.collapse_precursors(authority_scores, **kwargs)

    def reconstruct_for_future_steward(self, crr_id: str) -> dict[str, Any]:
        crr = self.crr_index.get(crr_id)
        if crr is None:
            event_id = self.store_event_index.get(crr_id)
            if event_id and event_id in self.store.nodes:
                return {
                    "crr_id": crr_id,
                    "reconstruction": dict(self.store.nodes[event_id].props),
                    "calibration_event": dict(self.store.nodes[event_id].props),
                    "transmissible": True,
                }
            return {"error": "crr_not_found", "crr_id": crr_id}

        replay = crr.reconstruct()
        event = next(
            (e for e in self.calibration_events.values() if e.crr_id == crr_id),
            None,
        )
        return {
            "crr_id": crr_id,
            "reconstruction": replay,
            "calibration_event": event.to_dict() if event else None,
            "transmissible": event is not None,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "wire_graph": {
                "nodes": [n.to_dict() for n in self.wire_graph.nodes.values()],
                "edges": [e.to_dict() for e in self.wire_graph.edges],
            },
            "clg": self.clg.to_dict(),
            "store": {
                "nodes": [
                    {"id": node.id, "kind": node.kind, "props": dict(node.props)}
                    for node in self.store.nodes.values()
                ],
                "edges": [
                    {"src": edge.src, "dst": edge.dst, "kind": edge.kind}
                    for edge in self.store.edges
                ],
            },
            "calibration_event_count": len(self.calibration_events) + len(
                [n for n in self.store.nodes.values() if n.kind == "CalibrationEvent"]
            ),
            "crr_count": len(self.crr_index) + len(self.store_event_index),
        }
