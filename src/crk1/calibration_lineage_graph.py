"""CLG-1 — Calibration Lineage Graph (full implementation)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from src.crk1.calibration_objects import CalibrationEvent
from src.crk1.correction_object import CalibrationCorrectionReceipt

CLGEdgeType = Literal[
    "corrects",
    "updates",
    "performed_by",
    "inherits_from",
    "influences",
    "observed_via",
]

CLGNodeType = Literal[
    "CalibrationEvent",
    "Steward",
    "Invariant",
    "DecisionCluster",
    "RealityChannel",
    "GRR",
]


@dataclass(frozen=True)
class CLGNode:
    id: str
    node_type: CLGNodeType
    label: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "node_type": self.node_type,
            "label": self.label,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CLGEdge:
    from_id: str
    to_id: str
    edge_type: CLGEdgeType

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_id": self.from_id,
            "to_id": self.to_id,
            "edge_type": self.edge_type,
        }


@dataclass
class CalibrationLineageGraphCLG1:
    """
    CLG-1 — append-only graph linking calibration events across time.

    Ingestion rule: every validated CRR-1 produces one CalibrationEvent vertex.
    """

    nodes: dict[str, CLGNode] = field(default_factory=dict)
    edges: list[CLGEdge] = field(default_factory=list)

    def _ensure_node(self, node: CLGNode) -> None:
        if node.id not in self.nodes:
            self.nodes[node.id] = node

    def ingest_crr(
        self,
        crr: CalibrationCorrectionReceipt,
        event: CalibrationEvent | None = None,
        *,
        decision_cluster_id: str | None = None,
        invariant_ids: list[str] | None = None,
    ) -> CalibrationEvent:
        """Ingest CRR-1 → CalibrationEvent + graph edges."""
        if event is None:
            event = CalibrationEvent(
                id=f"CEV-{crr.id}",
                crr_id=crr.id,
                steward_id=crr.created_by,
                channel_id=crr.correction.evidence.channel_id,
                expectation_ref=crr.correction.expectation.model_ref or crr.id,
                evidence_ref=crr.correction.evidence.evidence_ref,
                contradiction_ref=crr.id,
                surprise_ref=crr.id,
                correction_ref=crr.correction.id,
                calibration_delta=crr.correction.calibration.calibration_delta,
            )

        event_node = CLGNode(
            id=event.id,
            node_type="CalibrationEvent",
            label=f"Calibration {crr.id}",
            metadata=event.to_dict(),
        )
        steward_node = CLGNode(
            id=f"steward:{event.steward_id}",
            node_type="Steward",
            label=event.steward_id,
        )
        channel_node = CLGNode(
            id=f"channel:{event.channel_id}",
            node_type="RealityChannel",
            label=event.channel_id,
        )

        self._ensure_node(event_node)
        self._ensure_node(steward_node)
        self._ensure_node(channel_node)

        self.edges.append(CLGEdge(event.id, steward_node.id, "performed_by"))
        self.edges.append(CLGEdge(event.id, channel_node.id, "observed_via"))

        if decision_cluster_id:
            cluster = CLGNode(
                id=decision_cluster_id,
                node_type="DecisionCluster",
                label=decision_cluster_id,
            )
            self._ensure_node(cluster)
            self.edges.append(CLGEdge(event.id, decision_cluster_id, "corrects"))

        for inv_id in invariant_ids or event.invariant_implications:
            inv_node = CLGNode(id=f"invariant:{inv_id}", node_type="Invariant", label=inv_id)
            self._ensure_node(inv_node)
            self.edges.append(CLGEdge(event.id, inv_node.id, "updates"))

        for grr_id in event.related_grr_ids:
            grr_node = CLGNode(id=f"grr:{grr_id}", node_type="GRR", label=grr_id)
            self._ensure_node(grr_node)
            self.edges.append(CLGEdge(event.id, grr_node.id, "corrects"))

        return event

    def link_steward_handoff(self, from_steward: str, to_steward: str) -> None:
        """SHP handoff — inherits_from edge between stewards."""
        src = CLGNode(id=f"steward:{from_steward}", node_type="Steward", label=from_steward)
        dst = CLGNode(id=f"steward:{to_steward}", node_type="Steward", label=to_steward)
        self._ensure_node(src)
        self._ensure_node(dst)
        self.edges.append(CLGEdge(src.id, dst.id, "inherits_from"))

    def link_influence(self, from_event_id: str, to_event_id: str) -> None:
        self.edges.append(CLGEdge(from_event_id, to_event_id, "influences"))

    # Q1 — lineage of a correction / invariant
    def trace_invariant_lineage(self, invariant_id: str) -> list[CLGNode]:
        inv_node_id = f"invariant:{invariant_id}"
        event_ids = {
            edge.from_id
            for edge in self.edges
            if edge.to_id == inv_node_id and edge.edge_type == "updates"
        }
        return [self.nodes[eid] for eid in sorted(event_ids) if eid in self.nodes]

    # Q2 — steward calibration profile
    def steward_calibration_profile(self, steward_id: str) -> dict[str, Any]:
        sid = f"steward:{steward_id}"
        event_ids = {
            edge.from_id
            for edge in self.edges
            if edge.to_id == sid and edge.edge_type == "performed_by"
        }
        events = [self.nodes[eid] for eid in event_ids if eid in self.nodes]
        deltas = [
            float(node.metadata.get("calibration_delta", 0.0))
            for node in events
            if node.node_type == "CalibrationEvent"
        ]
        return {
            "steward_id": steward_id,
            "event_count": len(events),
            "calibration_delta_sum": sum(deltas),
            "density": len(events) / max(1, len(self.nodes)),
            "events": [e.to_dict() for e in events],
        }

    # Q3 — drift vs correction ratio
    def drift_correction_ratio(self, *, drift_index: float = 0.0) -> dict[str, Any]:
        event_count = sum(1 for n in self.nodes.values() if n.node_type == "CalibrationEvent")
        crr_density = event_count / max(1, len(self.nodes))
        ratio = crr_density / max(drift_index, 1e-9) if drift_index > 0 else float("inf")
        return {
            "drift_index": drift_index,
            "crr_density": crr_density,
            "event_count": event_count,
            "ratio": ratio,
        }

    # Q4 — collapse precursor: high authority stewards with low calibration degree
    def collapse_precursors(
        self,
        authority_scores: dict[str, float],
        *,
        calibration_threshold: float = 0.1,
    ) -> list[dict[str, Any]]:
        precursors: list[dict[str, Any]] = []
        for steward_id, authority in authority_scores.items():
            profile = self.steward_calibration_profile(steward_id)
            density = profile["density"]
            if authority > 0.7 and density < calibration_threshold:
                precursors.append(
                    {
                        "steward_id": steward_id,
                        "authority": authority,
                        "calibration_density": density,
                        "risk": "Type IV/V precursor — high authority, low calibration",
                    }
                )
        return precursors

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
        }
