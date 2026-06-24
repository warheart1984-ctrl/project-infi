"""Continuity graph builder — CRK-1 v0.1 wire objects to graph nodes and edges."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from src.crk1.crk1_wire_v01 import CRK1Envelope, ObjectType

RelationType = Literal[
    "initiated_by",
    "results_in",
    "documented_by",
    "supported_by",
    "interpreted_by",
    "influences",
    "authorized_by",
]


@dataclass(frozen=True)
class GraphNode:
    id: str
    type: ObjectType
    receipt_id: str
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "receipt_id": self.receipt_id,
            "label": self.label,
        }


@dataclass(frozen=True)
class GraphEdge:
    from_id: str
    to_id: str
    relation_type: RelationType

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_id": self.from_id,
            "to_id": self.to_id,
            "relation_type": self.relation_type,
        }


@dataclass
class GraphNodeView:
    node: GraphNode
    edges: list[GraphEdge] = field(default_factory=list)
    object: CRK1Envelope | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "node": self.node.to_dict(),
            "edges": [edge.to_dict() for edge in self.edges],
        }
        if self.object is not None:
            payload["object"] = self.object.to_dict()
        return payload


@dataclass
class ContinuityGraph:
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)
    objects: dict[str, CRK1Envelope] = field(default_factory=dict)

    def add_object(self, obj: CRK1Envelope | dict[str, Any]) -> None:
        envelope = obj if isinstance(obj, CRK1Envelope) else CRK1Envelope.model_validate(obj)
        self.objects[envelope.id] = envelope
        self.nodes[envelope.id] = GraphNode(
            id=envelope.id,
            type=envelope.type,
            receipt_id=envelope.receipt_id,
            label=envelope.label,
        )
        for edge in build_edges(envelope):
            if edge not in self.edges:
                self.edges.append(edge)

    def node_view(self, node_id: str) -> GraphNodeView:
        node = self.nodes[node_id]
        edges = [
            edge
            for edge in self.edges
            if edge.from_id == node_id or edge.to_id == node_id
        ]
        return GraphNodeView(node=node, edges=edges, object=self.objects.get(node_id))

    def chain_from(self, start_id: str) -> list[GraphNode]:
        """Linear continuity walk: Identity → Decision → Outcome → Evidence → Interpretation."""
        order = ("Identity", "Decision", "Outcome", "Evidence", "Interpretation")
        chain_ids: list[str] = [start_id]
        visited = {start_id}

        while True:
            extended = False
            for edge in self.edges:
                if edge.from_id in visited and edge.to_id not in visited:
                    chain_ids.append(edge.to_id)
                    visited.add(edge.to_id)
                    extended = True
                elif edge.to_id in visited and edge.from_id not in visited:
                    chain_ids.append(edge.from_id)
                    visited.add(edge.from_id)
                    extended = True
            if not extended:
                break

        nodes = [self.nodes[node_id] for node_id in chain_ids if node_id in self.nodes]
        continuity_types = set(order)
        filtered = [node for node in nodes if node.type in continuity_types]
        return sorted(filtered, key=lambda item: order.index(item.type))

    def graph_delta_for(self, obj: CRK1Envelope) -> dict[str, Any]:
        node = self.nodes[obj.id]
        edges = build_edges(obj)
        return {
            "nodes": [node.to_dict()],
            "edges": [edge.to_dict() for edge in edges],
        }


def build_edges(obj: CRK1Envelope) -> list[GraphEdge]:
    edges: list[GraphEdge] = []
    links = obj.links

    if obj.type == "Identity":
        for decision_id in links.get("decisions", []):
            edges.append(GraphEdge(obj.id, str(decision_id), "initiated_by"))

    elif obj.type == "Decision":
        identity_id = links.get("identity_id")
        if identity_id:
            edges.append(GraphEdge(str(identity_id), obj.id, "initiated_by"))
        for outcome_id in links.get("outcome_ids", []):
            edges.append(GraphEdge(obj.id, str(outcome_id), "results_in"))
        for evidence_id in links.get("evidence_ids", []):
            edges.append(GraphEdge(obj.id, str(evidence_id), "supported_by"))
        for interpretation_id in links.get("interpretation_ids", []):
            edges.append(GraphEdge(str(interpretation_id), obj.id, "influences"))

    elif obj.type == "Outcome":
        decision_id = links.get("decision_id")
        if decision_id:
            edges.append(GraphEdge(str(decision_id), obj.id, "results_in"))
        for evidence_id in links.get("evidence_ids", []):
            edges.append(GraphEdge(obj.id, str(evidence_id), "documented_by"))

    elif obj.type == "Evidence":
        outcome_id = links.get("outcome_id")
        if outcome_id:
            edges.append(GraphEdge(str(outcome_id), obj.id, "documented_by"))
        for interpretation_id in links.get("interpretation_ids", []):
            edges.append(GraphEdge(obj.id, str(interpretation_id), "interpreted_by"))

    elif obj.type == "Interpretation":
        for evidence_id in links.get("evidence_ids", []):
            edges.append(GraphEdge(str(evidence_id), obj.id, "interpreted_by"))
        decision_id = links.get("decision_id")
        if decision_id:
            edges.append(GraphEdge(obj.id, str(decision_id), "influences"))

    elif obj.type == "Receipt":
        object_id = links.get("object_id") or obj.payload.get("object_id")
        if object_id:
            edges.append(GraphEdge(obj.id, str(object_id), "authorized_by"))

    return edges


def load_walkthrough_graph(objects: list[dict[str, Any]]) -> ContinuityGraph:
    graph = ContinuityGraph()
    for item in objects:
        graph.add_object(item)
    return graph
