"""process_genome.v1 schema validation and graph helpers."""

from __future__ import annotations

from typing import Any

from mechanic.common import GENOME_SCHEMA_VERSION

NODE_TYPES = frozenset(
    {
        "prompt_asset",
        "agent_config",
        "workflow_automation",
        "tool_binding",
        "human_control",
        "model_call",
        "exception_path",
        "cost_center",
    }
)

EDGE_TYPES = frozenset(
    {
        "depends_on",
        "calls",
        "validates",
        "escalates_to_human",
        "exception_of",
        "shadow_of",
    }
)


class GenomeValidationError(ValueError):
    pass


def empty_genome(*, case_id: str, repo_path: str) -> dict[str, Any]:
    return {
        "schema_version": GENOME_SCHEMA_VERSION,
        "case_id": case_id,
        "repo_path": repo_path,
        "nodes": [],
        "edges": [],
        "adapters": [],
        "metadata": {},
    }


def validate_genome(genome: dict[str, Any]) -> None:
    if str(genome.get("schema_version") or "") != GENOME_SCHEMA_VERSION:
        raise GenomeValidationError(f"schema_version must be {GENOME_SCHEMA_VERSION}")
    if not str(genome.get("case_id") or "").strip():
        raise GenomeValidationError("case_id is required")
    nodes = genome.get("nodes")
    edges = genome.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise GenomeValidationError("nodes and edges must be lists")
    seen_ids: set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise GenomeValidationError(f"node[{index}] must be an object")
        node_id = str(node.get("id") or "").strip()
        if not node_id:
            raise GenomeValidationError(f"node[{index}] missing id")
        if node_id in seen_ids:
            raise GenomeValidationError(f"duplicate node id: {node_id}")
        seen_ids.add(node_id)
        node_type = str(node.get("type") or "")
        if node_type not in NODE_TYPES:
            raise GenomeValidationError(f"invalid node type: {node_type}")
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise GenomeValidationError(f"edge[{index}] must be an object")
        edge_type = str(edge.get("type") or "")
        if edge_type not in EDGE_TYPES:
            raise GenomeValidationError(f"invalid edge type: {edge_type}")
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if source not in seen_ids or target not in seen_ids:
            raise GenomeValidationError(f"edge references unknown node: {source} -> {target}")


def add_node(
    genome: dict[str, Any],
    *,
    node_id: str,
    node_type: str,
    label: str,
    source_path: str = "",
    attrs: dict[str, Any] | None = None,
) -> None:
    if node_type not in NODE_TYPES:
        raise GenomeValidationError(f"invalid node type: {node_type}")
    genome["nodes"].append(
        {
            "id": node_id,
            "type": node_type,
            "label": label,
            "source_path": source_path,
            "attrs": dict(attrs or {}),
        }
    )


def add_edge(
    genome: dict[str, Any],
    *,
    source: str,
    target: str,
    edge_type: str,
    attrs: dict[str, Any] | None = None,
) -> None:
    if edge_type not in EDGE_TYPES:
        raise GenomeValidationError(f"invalid edge type: {edge_type}")
    genome["edges"].append(
        {
            "source": source,
            "target": target,
            "type": edge_type,
            "attrs": dict(attrs or {}),
        }
    )


def nodes_by_type(genome: dict[str, Any], node_type: str) -> list[dict[str, Any]]:
    return [n for n in genome.get("nodes") or [] if str(n.get("type")) == node_type]


def model_call_nodes(genome: dict[str, Any]) -> list[dict[str, Any]]:
    return nodes_by_type(genome, "model_call")


def human_control_nodes(genome: dict[str, Any]) -> list[dict[str, Any]]:
    return nodes_by_type(genome, "human_control")
