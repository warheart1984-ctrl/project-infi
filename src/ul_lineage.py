"""UL Lineage Graph — append-only governance visibility for mission lifecycles."""

# Mythic: Ul Lineage
# Engineering: UlLineageEngine
from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LINEAGE_VERSION = "ul_lineage_graph.v1"
DEFAULT_LINEAGE_ROOT = Path(".runtime/lineage")
REQUIRED_NODE_TYPES = frozenset(
    {"chat_turn", "memory_promotion", "capability_call", "forge_handoff"}
)
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "ul_lineage_graph.v1.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def lineage_enabled() -> bool:
    return os.environ.get("AAIS_LINEAGE_ENABLED", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def lineage_root(root: Path | None = None) -> Path:
    return (root or DEFAULT_LINEAGE_ROOT).expanduser().resolve()


def graph_path(mission_id: str, *, root: Path | None = None) -> Path:
    return lineage_root(root) / mission_id / "ul_lineage_graph.v1.json"


def _stable_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _empty_graph(mission_id: str, *, session_id: str | None = None) -> dict[str, Any]:
    now = _utc_now_iso()
    return {
        "lineage_version": LINEAGE_VERSION,
        "graph_id": f"lineage-{mission_id}",
        "mission_id": mission_id,
        "session_id": session_id or "",
        "nodes": [],
        "edges": [],
        "claim_label": "asserted",
        "created_at_utc": now,
        "updated_at_utc": now,
    }


def _load_graph(mission_id: str, *, root: Path | None = None) -> dict[str, Any]:
    path = graph_path(mission_id, root=root)
    if not path.is_file():
        return _empty_graph(mission_id)
    return json.loads(path.read_text(encoding="utf-8"))


def _persist_graph(graph: dict[str, Any], *, root: Path | None = None) -> Path:
    mission_id = str(graph["mission_id"])
    path = graph_path(mission_id, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    graph["updated_at_utc"] = _utc_now_iso()
    path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def resolve_mission_id(
    *,
    session_id: str | None = None,
    session_metadata: dict[str, Any] | None = None,
    mission_id: str | None = None,
) -> str | None:
    if mission_id:
        return str(mission_id).strip() or None
    meta = dict(session_metadata or {})
    board = meta.get("mission_board") or {}
    active = board.get("active_mission") or {}
    if active.get("id"):
        return str(active["id"])
    if session_id:
        try:
            from src.mission_board import mission_board

            ctx = mission_board.build_session_context(session_id)
            active = ctx.get("active_mission") or {}
            if active.get("id"):
                return str(active["id"])
        except Exception:
            return None
    return None


def emit_node(
    mission_id: str,
    *,
    node_type: str,
    cisiv_stage: str,
    session_id: str | None = None,
    law_enforcement: dict[str, Any] | None = None,
    claim_label: str = "asserted",
    source_module: str = "",
    payload: dict[str, Any] | None = None,
    root: Path | None = None,
    link_previous: bool = True,
) -> dict[str, Any] | None:
    """Append one lineage node; optionally link temporally to the previous node."""
    if not lineage_enabled():
        return None
    if node_type not in REQUIRED_NODE_TYPES:
        raise ValueError(f"unsupported node_type: {node_type}")

    graph = _load_graph(mission_id, root=root)
    if session_id and not graph.get("session_id"):
        graph["session_id"] = session_id

    node_id = f"ln-{uuid.uuid4().hex[:16]}"
    node = {
        "node_id": node_id,
        "node_type": node_type,
        "timestamp_utc": _utc_now_iso(),
        "cisiv_stage": cisiv_stage,
        "source_module": source_module,
        "claim_label": claim_label,
    }
    if law_enforcement:
        node["law_enforcement"] = law_enforcement
    if payload:
        node["payload_hash"] = _stable_hash(payload)

    graph["nodes"].append(node)
    if link_previous and len(graph["nodes"]) >= 2:
        prev = graph["nodes"][-2]["node_id"]
        graph["edges"].append(
            {
                "edge_id": f"le-{uuid.uuid4().hex[:16]}",
                "from_node_id": prev,
                "to_node_id": node_id,
                "edge_type": "temporal",
                "drift_checked": False,
            }
        )
    _persist_graph(graph, root=root)
    return node


def link_nodes(
    mission_id: str,
    *,
    from_node_id: str,
    to_node_id: str,
    edge_type: str = "causal",
    drift_checked: bool = False,
    root: Path | None = None,
) -> dict[str, Any] | None:
    if not lineage_enabled():
        return None
    graph = _load_graph(mission_id, root=root)
    edge = {
        "edge_id": f"le-{uuid.uuid4().hex[:16]}",
        "from_node_id": from_node_id,
        "to_node_id": to_node_id,
        "edge_type": edge_type,
        "drift_checked": drift_checked,
    }
    graph["edges"].append(edge)
    _persist_graph(graph, root=root)
    return edge


def build_graph(mission_id: str, *, session_id: str | None = None, root: Path | None = None) -> dict[str, Any]:
    graph = _load_graph(mission_id, root=root)
    if session_id and not graph.get("session_id"):
        graph["session_id"] = session_id
    return graph


def validate_graph(graph: dict[str, Any]) -> dict[str, Any]:
    """Validate graph shape and required node-type coverage."""
    failures: list[str] = []
    if graph.get("lineage_version") != LINEAGE_VERSION:
        failures.append("invalid lineage_version")
    if not graph.get("mission_id"):
        failures.append("missing mission_id")
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    if not isinstance(nodes, list):
        failures.append("nodes must be a list")
        nodes = []
    if not isinstance(edges, list):
        failures.append("edges must be a list")
        edges = []

    seen_types = {n.get("node_type") for n in nodes if isinstance(n, dict)}
    missing_types = sorted(REQUIRED_NODE_TYPES - seen_types)
    if missing_types:
        failures.append(f"missing node types: {', '.join(missing_types)}")

    for node in nodes:
        if not isinstance(node, dict):
            failures.append("invalid node entry")
            continue
        for key in ("node_id", "node_type", "timestamp_utc", "cisiv_stage"):
            if not node.get(key):
                failures.append(f"node missing {key}")

    multi_hop = len(nodes) >= 2 and len(edges) >= 1
    if nodes and not multi_hop:
        failures.append("expected multi-hop graph with at least one edge")

    passed = not failures
    return {
        "passed": passed,
        "failures": failures,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_types_present": sorted(t for t in seen_types if t),
    }


def record_lineage_event(
    *,
    node_type: str,
    cisiv_stage: str,
    session_id: str | None = None,
    session_metadata: dict[str, Any] | None = None,
    mission_id: str | None = None,
    law_enforcement: dict[str, Any] | None = None,
    claim_label: str = "asserted",
    source_module: str = "",
    payload: dict[str, Any] | None = None,
    root: Path | None = None,
) -> dict[str, Any] | None:
    """Resolve mission and emit; skip silently when no mission is bound."""
    try:
        resolved = resolve_mission_id(
            session_id=session_id,
            session_metadata=session_metadata,
            mission_id=mission_id,
        )
        if not resolved:
            return None
        return emit_node(
            resolved,
            node_type=node_type,
            cisiv_stage=cisiv_stage,
            session_id=session_id,
            law_enforcement=law_enforcement,
            claim_label=claim_label,
            source_module=source_module,
            payload=payload,
            root=root,
        )
    except Exception:
        return None
