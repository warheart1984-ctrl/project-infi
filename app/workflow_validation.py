from __future__ import annotations

from typing import Any


SUPPORTED_TRIGGER_TYPES = {
    "email.received",
    "slack.message",
    "webhook.received",
    "schedule.tick",
    "manual",
}

SUPPORTED_ACTION_TYPES = {
    "ai.analyze",
    "slack.send",
    "email.send",
    "api.call",
    "task.create",
}

SUPPORTED_CONDITION_TYPES = {
    "contains_text",
    "high_priority",
    "from_domain",
    "confidence_above",
}

SUPPORTED_STEP_TYPES = SUPPORTED_ACTION_TYPES | {
    f"condition.{condition_type}" for condition_type in SUPPORTED_CONDITION_TYPES
}

MAX_WORKFLOW_STEPS = 25
WORKFLOW_SCHEMA_VERSION = 1


class WorkflowValidationError(ValueError):
    pass


def _clean_label(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    return text or fallback


def _normalize_edge(edge: dict[str, Any], index: int) -> dict[str, Any]:
    source = str(edge.get("source") or "").strip()
    target = str(edge.get("target") or "").strip()
    if not source or not target:
        raise WorkflowValidationError("Each connection must have both a source and a target.")
    if source == target:
        raise WorkflowValidationError("A workflow node cannot connect to itself.")
    return {
        "id": str(edge.get("id") or f"edge-{index + 1}"),
        "source": source,
        "sourceHandle": edge.get("sourceHandle"),
        "target": target,
    }


def _compute_linear_step_order(
    trigger_id: str | None,
    step_nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[str]:
    if not step_nodes:
        raise WorkflowValidationError("Add at least one workflow step before saving.")

    if not edges:
        raise WorkflowValidationError("Connect the trigger to at least one step before saving.")

    outgoing: dict[str, list[str]] = {}
    incoming: dict[str, int] = {step_id: 0 for step_id in step_nodes}

    for edge in edges:
        outgoing.setdefault(edge["source"], []).append(edge["target"])
        if edge["target"] in incoming:
            incoming[edge["target"]] += 1

    for source, targets in outgoing.items():
        if len(targets) > 1:
            raise WorkflowValidationError(
                "Branching workflows are not supported yet. Keep each node on a single outgoing path."
            )

    if trigger_id:
        trigger_targets = outgoing.get(trigger_id, [])
        if len(trigger_targets) != 1:
            raise WorkflowValidationError("Connect the trigger to exactly one starting step.")
        current = trigger_targets[0]
    else:
        roots = [step_id for step_id, count in incoming.items() if count == 0]
        if len(roots) != 1:
            raise WorkflowValidationError("Workflow steps must form one connected path.")
        current = roots[0]

    ordered: list[str] = []
    visited: set[str] = set()

    while current is not None:
        if current in visited:
            raise WorkflowValidationError("Workflow connections create a cycle. Remove the loop and try again.")
        if current not in step_nodes:
            raise WorkflowValidationError("Every connection must point to a valid workflow step.")
        visited.add(current)
        ordered.append(current)
        next_targets = outgoing.get(current, [])
        current = next_targets[0] if next_targets else None

    if len(visited) != len(step_nodes):
        raise WorkflowValidationError("Connect all steps into a single path from the trigger before saving.")

    return ordered


def build_workflow_config_from_graph(
    name: str,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    workflow_name = _clean_label(name, "Untitled Workflow")
    if not nodes:
        raise WorkflowValidationError("Add a trigger and at least one step before saving.")

    node_ids: set[str] = set()
    trigger_node: dict[str, Any] | None = None
    step_nodes: dict[str, dict[str, Any]] = {}

    for index, node in enumerate(nodes):
        node_id = str(node.get("id") or "").strip()
        if not node_id:
            raise WorkflowValidationError("Every workflow node needs an id.")
        if node_id in node_ids:
            raise WorkflowValidationError("Workflow node ids must be unique.")
        node_ids.add(node_id)

        data = node.get("data") or {}
        kind = str(data.get("kind") or "").strip()
        subtype = str(data.get("subtype") or "").strip()
        label = _clean_label(data.get("label"), f"Step {index + 1}")
        config = data.get("config") or {}
        if not isinstance(config, dict):
            raise WorkflowValidationError("Each workflow node config must be an object.")

        normalized = {
            "id": node_id,
            "label": label,
            "kind": kind,
            "subtype": subtype,
            "config": config,
        }

        if kind == "trigger":
            if trigger_node is not None:
                raise WorkflowValidationError("Use exactly one trigger per workflow.")
            if subtype not in SUPPORTED_TRIGGER_TYPES:
                raise WorkflowValidationError(f"Unsupported trigger type: {subtype}")
            trigger_node = normalized
        elif kind == "action":
            if subtype not in SUPPORTED_ACTION_TYPES:
                raise WorkflowValidationError(f"Unsupported action type: {subtype}")
            step_nodes[node_id] = normalized
        elif kind == "condition":
            if subtype not in SUPPORTED_CONDITION_TYPES:
                raise WorkflowValidationError(f"Unsupported condition type: {subtype}")
            step_nodes[node_id] = normalized
        else:
            raise WorkflowValidationError(f"Unsupported workflow node kind: {kind}")

    if trigger_node is None:
        raise WorkflowValidationError("Add exactly one trigger before saving.")

    if len(step_nodes) > MAX_WORKFLOW_STEPS:
        raise WorkflowValidationError(f"Workflows currently support up to {MAX_WORKFLOW_STEPS} steps.")

    normalized_edges = [_normalize_edge(edge, index) for index, edge in enumerate(edges)]
    for edge in normalized_edges:
        if edge["source"] not in node_ids or edge["target"] not in node_ids:
            raise WorkflowValidationError("Every connection must point to nodes that exist in the workflow.")

    ordered_step_ids = _compute_linear_step_order(trigger_node["id"], step_nodes, normalized_edges)

    return {
        "schemaVersion": WORKFLOW_SCHEMA_VERSION,
        "name": workflow_name,
        "trigger": {
            "id": trigger_node["id"],
            "type": trigger_node["subtype"],
            "label": trigger_node["label"],
            "config": trigger_node["config"],
        },
        "steps": [
            {
                "id": step_id,
                "order": index + 1,
                "type": (
                    f"condition.{step_nodes[step_id]['subtype']}"
                    if step_nodes[step_id]["kind"] == "condition"
                    else step_nodes[step_id]["subtype"]
                ),
                "label": step_nodes[step_id]["label"],
                "config": step_nodes[step_id]["config"],
            }
            for index, step_id in enumerate(ordered_step_ids)
        ],
        "edges": normalized_edges,
    }


def validate_workflow_config(config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise WorkflowValidationError("Workflow config must be an object.")

    raw_schema_version = config.get("schemaVersion", WORKFLOW_SCHEMA_VERSION)
    try:
        schema_version = int(raw_schema_version)
    except (TypeError, ValueError) as exc:
        raise WorkflowValidationError("Workflow schemaVersion must be a number.") from exc
    if schema_version != WORKFLOW_SCHEMA_VERSION:
        raise WorkflowValidationError(
            f"Unsupported workflow schemaVersion: {schema_version}. Expected {WORKFLOW_SCHEMA_VERSION}."
        )

    workflow_name = _clean_label(config.get("name"), "Untitled Workflow")
    trigger = config.get("trigger")
    if trigger is not None:
        if not isinstance(trigger, dict):
            raise WorkflowValidationError("Workflow trigger must be an object.")
        trigger_type = str(trigger.get("type") or "").strip()
        if trigger_type not in SUPPORTED_TRIGGER_TYPES:
            raise WorkflowValidationError(f"Unsupported trigger type: {trigger_type}")
        normalized_trigger = {
            "id": trigger.get("id"),
            "type": trigger_type,
            "label": _clean_label(trigger.get("label"), "Trigger"),
            "config": trigger.get("config") if isinstance(trigger.get("config"), dict) else {},
        }
    else:
        normalized_trigger = None

    raw_steps = config.get("steps") or []
    if not isinstance(raw_steps, list) or not raw_steps:
        raise WorkflowValidationError("Add at least one workflow step before running.")
    if len(raw_steps) > MAX_WORKFLOW_STEPS:
        raise WorkflowValidationError(f"Workflows currently support up to {MAX_WORKFLOW_STEPS} steps.")

    step_map: dict[str, dict[str, Any]] = {}
    for index, raw_step in enumerate(raw_steps):
        if not isinstance(raw_step, dict):
            raise WorkflowValidationError("Workflow steps must be objects.")
        step_id = str(raw_step.get("id") or "").strip()
        if not step_id:
            raise WorkflowValidationError("Every workflow step needs an id.")
        if step_id in step_map:
            raise WorkflowValidationError("Workflow step ids must be unique.")
        step_type = str(raw_step.get("type") or "").strip()
        if step_type not in SUPPORTED_STEP_TYPES:
            raise WorkflowValidationError(f"Unsupported workflow step type: {step_type}")
        step_map[step_id] = {
            "id": step_id,
            "order": int(raw_step.get("order") or index + 1),
            "type": step_type,
            "label": _clean_label(raw_step.get("label"), f"Step {index + 1}"),
            "config": raw_step.get("config") if isinstance(raw_step.get("config"), dict) else {},
        }

    raw_edges = config.get("edges") or []
    if not isinstance(raw_edges, list):
        raise WorkflowValidationError("Workflow edges must be a list.")
    normalized_edges = [_normalize_edge(edge, index) for index, edge in enumerate(raw_edges)]

    if normalized_edges and normalized_trigger and normalized_trigger.get("id"):
        ordered_step_ids = _compute_linear_step_order(
            str(normalized_trigger["id"]),
            step_map,
            normalized_edges,
        )
    else:
        ordered_step_ids = [step_id for step_id, _ in sorted(step_map.items(), key=lambda item: (item[1]["order"], item[0]))]

    normalized_steps = [
        {
            **step_map[step_id],
            "order": index + 1,
        }
        for index, step_id in enumerate(ordered_step_ids)
    ]

    return {
        "schemaVersion": schema_version,
        "name": workflow_name,
        "trigger": normalized_trigger,
        "steps": normalized_steps,
        "edges": normalized_edges,
    }
