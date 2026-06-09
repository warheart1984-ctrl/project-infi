"""Test-phase validators: cycles, orphans, leaps, evidence."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.rls.reasoning_graph import is_valid_evidence_ref


def _node_map(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(n["id"]): n for n in (graph.get("nodes") or []) if n.get("id")}


def _inbound_edges(graph: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    inbound: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in graph.get("edges") or []:
        inbound[str(edge.get("to"))].append(edge)
    return inbound


def _outbound_edges(graph: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    outbound: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in graph.get("edges") or []:
        outbound[str(edge.get("from"))].append(edge)
    return outbound


def check_orphan_conclusion(graph: dict[str, Any]) -> list[dict[str, Any]]:
    conclusion_id = str(graph.get("conclusion_id") or "")
    inbound = _inbound_edges(graph)
    if conclusion_id and not inbound.get(conclusion_id):
        return [
            {
                "code": "orphan_conclusion",
                "severity": "error",
                "node_ids": [conclusion_id],
                "detail": "Conclusion has no inbound support or derivation path",
            }
        ]
    return []


def check_circular_reasoning(graph: dict[str, Any]) -> list[dict[str, Any]]:
    outbound = _outbound_edges(graph)
    nodes = _node_map(graph)
    visited: set[str] = set()
    stack: set[str] = set()
    cycle_nodes: list[str] = []

    def dfs(node_id: str) -> bool:
        if node_id in stack:
            cycle_nodes.append(node_id)
            return True
        if node_id in visited:
            return False
        visited.add(node_id)
        stack.add(node_id)
        for edge in outbound.get(node_id, []):
            if dfs(str(edge.get("to"))):
                cycle_nodes.append(node_id)
                return True
        stack.remove(node_id)
        return False

    for nid in nodes:
        if dfs(nid):
            return [
                {
                    "code": "circular_reasoning",
                    "severity": "error",
                    "node_ids": list(dict.fromkeys(cycle_nodes)),
                    "detail": "Support graph contains a cycle",
                }
            ]
    return []


def _is_benign_adapter_derivation(
    node: dict[str, Any],
    graph: dict[str, Any],
    *,
    action_intent: str,
) -> bool:
    """Standard flat-text/Jarvis derivation that restates the conclusion structurally."""
    kind = str(node.get("kind") or "").lower()
    if kind != "inference":
        return False
    text = str(node.get("text") or "").lower()
    if not (text.startswith("therefore:") or text.startswith("synthesis toward:")):
        return False
    if "predict" in text and "approv" in text:
        return False
    if action_intent and action_intent in text:
        return False
    nid = str(node.get("id") or "")
    return bool(_inbound_edges(graph).get(nid))


def check_self_justifying_loop(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect when conclusion or proposed action is cited as sole evidence."""
    nodes = _node_map(graph)
    conclusion_id = str(graph.get("conclusion_id") or "")
    conclusion = nodes.get(conclusion_id, {})
    conclusion_text = str(conclusion.get("text") or "").strip().lower()
    proposed = dict(graph.get("proposed_action") or {})
    action_intent = str(proposed.get("intent") or "").strip().lower()

    violations: list[dict[str, Any]] = []
    for node in graph.get("nodes") or []:
        if _is_benign_adapter_derivation(node, graph, action_intent=action_intent):
            continue
        nid = str(node.get("id") or "")
        if nid == conclusion_id:
            # Terminal conclusion restating itself is structural, not self-justification.
            continue
        refs = [str(r).strip().lower() for r in (node.get("evidence_refs") or [])]
        text = str(node.get("text") or "").lower()
        if not refs and not text:
            continue

        cites_conclusion = (
            conclusion_text
            and (
                conclusion_text in text
                or any(conclusion_text in r for r in refs)
                or conclusion_id.lower() in refs
            )
        )
        cites_action = action_intent and (action_intent in text or any(action_intent in r for r in refs))
        predicts_approval = "predict" in text and "approv" in text

        if cites_conclusion or cites_action or predicts_approval:
            sole_evidence = len(refs) <= 1 and not any(is_valid_evidence_ref(r) for r in refs)
            if sole_evidence or predicts_approval:
                violations.append(
                    {
                        "code": "self_justifying_loop",
                        "severity": "error",
                        "node_ids": [nid],
                        "detail": "Node cites conclusion or predicted approval as sole justification",
                    }
                )
    return violations


def check_missing_evidence(graph: dict[str, Any], *, strict: bool) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    conclusion_id = str(graph.get("conclusion_id") or "")
    for node in graph.get("nodes") or []:
        nid = str(node.get("id") or "")
        kind = str(node.get("kind") or "").lower()
        refs = list(node.get("evidence_refs") or [])
        if kind in ("conclusion", "inference") or nid == conclusion_id:
            valid_refs = [r for r in refs if is_valid_evidence_ref(r)]
            if not valid_refs:
                severity = "error" if strict else "warning"
                violations.append(
                    {
                        "code": "missing_evidence",
                        "severity": severity,
                        "node_ids": [nid],
                        "detail": "Node lacks structured evidence refs (odl/ugr/ir/log/external)",
                    }
                )
    return violations


def check_unsupported_leap(graph: dict[str, Any]) -> list[dict[str, Any]]:
    inbound = _inbound_edges(graph)
    violations: list[dict[str, Any]] = []
    for node in graph.get("nodes") or []:
        if str(node.get("kind") or "").lower() != "inference":
            continue
        nid = str(node.get("id") or "")
        if not inbound.get(nid):
            violations.append(
                {
                    "code": "unsupported_leap",
                    "severity": "error",
                    "node_ids": [nid],
                    "detail": "Inference node has no supporting inbound edge",
                }
            )
    return violations


def check_speculative_at_ceiling(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag speculative language at hyper_strict ceiling."""
    speculative_markers = ("maybe", "might", "could", "possibly", "predict", "assume", "guess")
    violations: list[dict[str, Any]] = []
    for node in graph.get("nodes") or []:
        text = str(node.get("text") or "").lower()
        nid = str(node.get("id") or "")
        if any(marker in text for marker in speculative_markers):
            violations.append(
                {
                    "code": "speculative_at_ceiling",
                    "severity": "error",
                    "node_ids": [nid],
                    "detail": "Speculative reasoning not allowed at sovereign ceiling",
                }
            )
    return violations


def run_test_phase(
    graph: dict[str, Any],
    *,
    mode: str,
) -> list[dict[str, Any]]:
    """Aggregate structural and evidence validators."""
    strict_evidence = mode in ("paranoid", "hyper_strict")
    violations: list[dict[str, Any]] = []
    violations.extend(check_orphan_conclusion(graph))
    violations.extend(check_circular_reasoning(graph))
    violations.extend(check_self_justifying_loop(graph))
    violations.extend(check_unsupported_leap(graph))
    violations.extend(check_missing_evidence(graph, strict=strict_evidence))
    if mode == "hyper_strict":
        violations.extend(check_speculative_at_ceiling(graph))
    return violations
