"""CLG-1 graph store abstraction — in-memory backend and query surface."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class CLG1Node:
    id: str
    kind: str
    props: dict[str, Any] = field(default_factory=dict)


@dataclass
class CLG1Edge:
    src: str
    dst: str
    kind: str


class CLG1Store(Protocol):
    """Graph backend for CLG-1 ingestion and lineage queries."""

    def create_node(self, kind: str, props: dict[str, Any]) -> str: ...

    def ensure_node(self, node_id: str, kind: str, props: dict[str, Any] | None = None) -> str: ...

    def create_edge(self, src: str, dst: str, kind: str) -> None: ...

    def query(self, cypher: str, params: dict[str, Any]) -> list[dict[str, Any]]: ...


@dataclass
class InMemoryCLG1Store:
    """In-memory CLG-1 store with minimal Cypher-style query support."""

    nodes: dict[str, CLG1Node] = field(default_factory=dict)
    edges: list[CLG1Edge] = field(default_factory=list)

    def create_node(self, kind: str, props: dict[str, Any]) -> str:
        node_id = f"{kind}:{uuid.uuid4().hex[:12]}"
        self.nodes[node_id] = CLG1Node(id=node_id, kind=kind, props=dict(props))
        return node_id

    def ensure_node(self, node_id: str, kind: str, props: dict[str, Any] | None = None) -> str:
        if node_id not in self.nodes:
            self.nodes[node_id] = CLG1Node(id=node_id, kind=kind, props=dict(props or {}))
        elif props:
            self.nodes[node_id].props.update(props)
        return node_id

    def create_edge(self, src: str, dst: str, kind: str) -> None:
        self.edges.append(CLG1Edge(src=src, dst=dst, kind=kind))

    def query(self, cypher: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        normalized = " ".join(cypher.split())

        if "PERFORMED_CALIBRATION" in normalized and "Steward" in normalized:
            steward_id = str(params.get("sid", ""))
            steward_key = steward_id if steward_id.startswith("Steward:") else f"Steward:{steward_id}"
            events = []
            for edge in self.edges:
                if edge.src == steward_key and edge.kind == "PERFORMED_CALIBRATION":
                    node = self.nodes.get(edge.dst)
                    if node and node.kind == "CalibrationEvent":
                        events.append(node)
            events.sort(key=lambda node: node.props.get("timestamp_utc", ""))
            return [{"e": dict(node.props)} for node in events]

        if "CORRECTS_DECISION" in normalized and "Decision" in normalized:
            decision_id = str(params.get("did", ""))
            decision_key = decision_id if decision_id.startswith("Decision:") else f"Decision:{decision_id}"
            events = []
            for edge in self.edges:
                if edge.src == decision_key and edge.kind == "CORRECTS_DECISION":
                    node = self.nodes.get(edge.dst)
                    if node and node.kind == "CalibrationEvent":
                        events.append(node)
            events.sort(key=lambda node: node.props.get("timestamp_utc", ""))
            return [{"e": dict(node.props)} for node in events]

        return []
