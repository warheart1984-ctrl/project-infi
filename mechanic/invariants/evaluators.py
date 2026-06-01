"""Pure deterministic invariant evaluators over Process Genome graphs."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

from mechanic.invariants.codes import format_drift

_CATALOG_PATH = Path(__file__).resolve().parent / "ai_workflow_invariants.v1.json"

Genome = dict[str, Any]
EvaluatorFn = Callable[[Genome, dict[str, Any]], list[dict[str, Any]]]


def load_invariant_catalog() -> dict[str, Any]:
    return json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))


def _nodes(genome: Genome, node_type: str) -> list[dict[str, Any]]:
    return [n for n in genome.get("nodes") or [] if str(n.get("type")) == node_type]


def _edges_from(genome: Genome, source_id: str) -> list[dict[str, Any]]:
    return [e for e in genome.get("edges") or [] if str(e.get("source")) == source_id]


def _edges_to(genome: Genome, target_id: str) -> list[dict[str, Any]]:
    return [e for e in genome.get("edges") or [] if str(e.get("target")) == target_id]


def check_decision_owner(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    for wf in _nodes(genome, "workflow_automation"):
        attrs = wf.get("attrs") or {}
        if not attrs.get("owner") and not attrs.get("decision_owner"):
            drifts.append(
                format_drift(
                    code="GOV-01",
                    summary=f"workflow {wf.get('label')} lacks decision owner metadata",
                    evidence={"node_id": wf.get("id"), "source_path": wf.get("source_path")},
                    ma13_class="II",
                    severity="high",
                )
            )
    if len(_nodes(genome, "model_call")) >= 2 and not _nodes(genome, "agent_config"):
        drifts.append(
            format_drift(
                code="GOV-01",
                summary="multiple model calls without agent_config owner node",
                evidence={"model_call_count": len(_nodes(genome, "model_call"))},
                ma13_class="II",
                severity="high",
            )
        )
    return drifts


def check_exception_surface(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    model_calls = _nodes(genome, "model_call")
    exceptions = _nodes(genome, "exception_path")
    if model_calls and not exceptions:
        for mc in model_calls[:3]:
            drifts.append(
                format_drift(
                    code="GOV-12",
                    summary=f"model call at {mc.get('source_path')} has no linked exception_path",
                    evidence={"node_id": mc.get("id"), "source_path": mc.get("source_path")},
                    ma13_class="II",
                    severity="high",
                )
            )
        if len(model_calls) > 3:
            drifts[-1]["evidence"]["additional_model_calls"] = len(model_calls) - 3
    return drifts


def check_prompt_governance(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    for prompt in _nodes(genome, "prompt_asset"):
        attrs = prompt.get("attrs") or {}
        path = str(prompt.get("source_path") or "")
        if attrs.get("from_cursor"):
            continue
        if ".cursor/" in path:
            continue
        if "governed" in path.lower() or "doctrine" in path.lower():
            continue
        if path.endswith(".md") and "README" in path.upper():
            continue
        drifts.append(
            format_drift(
                code="GOV-15",
                summary=f"prompt asset may lack governance metadata: {prompt.get('label')}",
                evidence={"node_id": prompt.get("id"), "source_path": path},
                ma13_class="II",
                severity="medium",
            )
        )
    return drifts[:5]


def check_self_loop_boundary(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in genome.get("edges") or []:
        adjacency[str(edge.get("source"))].append(str(edge.get("target")))
    visited: set[str] = set()
    stack: set[str] = set()

    def dfs(node: str) -> bool:
        if node in stack:
            return True
        if node in visited:
            return False
        visited.add(node)
        stack.add(node)
        for nxt in adjacency.get(node, []):
            if dfs(nxt):
                return True
        stack.remove(node)
        return False

    for node in adjacency:
        if dfs(node):
            drifts.append(
                format_drift(
                    code="RNT-04",
                    summary="cycle detected in workflow graph without invariant boundary",
                    evidence={"node_id": node},
                    ma13_class="III",
                    severity="critical",
                )
            )
            break
    retry_loops = [
        n
        for n in _nodes(genome, "prompt_asset")
        if "retry" in str(n.get("label") or "").lower()
        or "loop" in str((n.get("attrs") or {}).get("content_hint") or "").lower()
    ]
    if len(_nodes(genome, "model_call")) >= 4 and not retry_loops:
        drifts.append(
            format_drift(
                code="RNT-04",
                summary="high model_call density suggests unbounded agent loop risk",
                evidence={"model_call_count": len(_nodes(genome, "model_call"))},
                ma13_class="III",
                severity="critical",
            )
        )
    return drifts


def check_output_validation(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    validators = [n for n in genome.get("nodes") or [] if "validat" in str(n.get("label") or "").lower()]
    has_validate_edge = any(str(e.get("type")) == "validates" for e in genome.get("edges") or [])
    if _nodes(genome, "model_call") and not validators and not has_validate_edge:
        drifts.append(
            format_drift(
                code="RNT-08",
                summary="no output validation node or validates edge on model_call chain",
                evidence={"model_call_count": len(_nodes(genome, "model_call"))},
                ma13_class="II",
                severity="high",
            )
        )
    return drifts


def check_audit_hooks(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    for mc in _nodes(genome, "model_call"):
        attrs = mc.get("attrs") or {}
        if not attrs.get("audit") and not attrs.get("trace_id"):
            path = str(mc.get("source_path") or "")
            if "test" in path.lower():
                continue
            drifts.append(
                format_drift(
                    code="RNT-11",
                    summary=f"model call missing audit hook metadata at {path}",
                    evidence={"node_id": mc.get("id"), "source_path": path},
                    ma13_class="III",
                    severity="medium",
                )
            )
    return drifts[:5]


def check_redundant_model_calls(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    by_path: dict[str, int] = defaultdict(int)
    for mc in _nodes(genome, "model_call"):
        key = str(mc.get("source_path") or mc.get("id"))
        by_path[key] += 1
    for path, count in by_path.items():
        if count >= 2:
            drifts.append(
                format_drift(
                    code="CST-07",
                    summary=f"redundant model calls ({count}) in {path}",
                    evidence={"source_path": path, "count": count},
                    severity="medium",
                )
            )
    return drifts


def check_cost_center_tagging(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    ci_models = [
        mc
        for mc in _nodes(genome, "model_call")
        if str(mc.get("source_path") or "").startswith(".github/")
    ]
    cost_centers = _nodes(genome, "cost_center")
    if ci_models and not cost_centers:
        drifts.append(
            format_drift(
                code="CST-09",
                summary="CI model_call steps lack cost_center nodes",
                evidence={"ci_model_calls": len(ci_models)},
                severity="low",
            )
        )
    return drifts


def check_human_control_substitute(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    metadata = genome.get("metadata") or {}
    if metadata.get("fixture_profile") == "missing_hitl":
        drifts.append(
            format_drift(
                code="HUM-03",
                summary="fixture encodes removed human control without substitute",
                evidence={"fixture_profile": "missing_hitl"},
                ma13_class="II",
                severity="high",
            )
        )
    if len(_nodes(genome, "model_call")) >= 3 and not _nodes(genome, "human_control"):
        drifts.append(
            format_drift(
                code="HUM-03",
                summary="automated model chain lacks human_control nodes",
                evidence={"model_call_count": len(_nodes(genome, "model_call"))},
                ma13_class="II",
                severity="high",
            )
        )
    return drifts


def check_hitl_on_high_impact(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    high_impact = [
        wf
        for wf in _nodes(genome, "workflow_automation")
        if (wf.get("attrs") or {}).get("high_impact") or (wf.get("attrs") or {}).get("llm_hint")
    ]
    if high_impact and not _nodes(genome, "human_control"):
        drifts.append(
            format_drift(
                code="HUM-05",
                summary="high-impact workflow lacks human-in-the-loop step",
                evidence={"workflow_ids": [w.get("id") for w in high_impact]},
                ma13_class="II",
                severity="medium",
            )
        )
    return drifts


def check_shadow_workflows(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    labels: dict[str, list[str]] = defaultdict(list)
    for wf in _nodes(genome, "workflow_automation"):
        label = str(wf.get("label") or "").lower()
        labels[label].append(str(wf.get("id")))
    for label, ids in labels.items():
        if len(ids) > 1 and label:
            drifts.append(
                format_drift(
                    code="GOV-20",
                    summary=f"duplicate workflow label may indicate shadow process: {label}",
                    evidence={"node_ids": ids},
                    ma13_class="II",
                    severity="medium",
                )
            )
    return drifts


def _repo_root(genome: Genome) -> Path:
    return Path(str(genome.get("repo_path") or ".")).expanduser().resolve()


def _read_prompt_text(genome: Genome, prompt: dict[str, Any]) -> str:
    rel = str(prompt.get("source_path") or "").strip()
    if not rel:
        return ""
    path = _repo_root(genome) / rel
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def check_prompt_stage2_fidelity(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    from src.stage2_fidelity_metrics import (
        detect_dropped_constraint,
        detect_smuggled_goal,
        detect_unauthorized_tool,
    )

    drifts: list[dict[str, Any]] = []
    for prompt in _nodes(genome, "prompt_asset"):
        content = _read_prompt_text(genome, prompt)
        if not content.strip():
            continue
        path = str(prompt.get("source_path") or "")
        for detector, code, ma13, summary_prefix in (
            (detect_smuggled_goal, "HUM-03", "I", "Stage 2 usurpation language in prompt asset"),
            (detect_dropped_constraint, "GOV-15", "II", "Stage 2 constraint dismissal in prompt asset"),
            (detect_unauthorized_tool, "HUM-08", "III", "Unauthorized actuation language in prompt asset"),
        ):
            if detector is detect_smuggled_goal:
                finding = detector(user_message="", assistant_reply=content)
            elif detector is detect_dropped_constraint:
                finding = detector(user_message="must not skip constraints", assistant_reply=content)
            else:
                finding = detector(assistant_reply=content)
            if finding:
                drifts.append(
                    format_drift(
                        code=code,
                        summary=f"{summary_prefix}: {prompt.get('label')}",
                        evidence={
                            "node_id": prompt.get("id"),
                            "source_path": path,
                            "detector_id": finding.detector_id,
                            "violation_class": finding.violation_class,
                        },
                        ma13_class=ma13 if ma13 != "I" else "I",
                        severity="high" if ma13 in {"I", "III"} else "medium",
                    )
                )
                break
    return drifts[:8]


def check_rollback_metadata(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    for wf in _nodes(genome, "workflow_automation"):
        attrs = wf.get("attrs") or {}
        if attrs.get("high_impact") or attrs.get("llm_hint"):
            if not attrs.get("rollback_token") and not attrs.get("rollback_plan"):
                drifts.append(
                    format_drift(
                        code="GOV-25",
                        summary=f"high-impact workflow {wf.get('label')} missing rollback metadata",
                        evidence={"node_id": wf.get("id"), "source_path": wf.get("source_path")},
                        ma13_class="II",
                        severity="medium",
                    )
                )
    return drifts


def check_extraction_provenance(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    metadata = genome.get("metadata") or {}
    if not metadata.get("extracted_at_utc"):
        return [
            format_drift(
                code="GOV-30",
                summary="genome metadata missing extracted_at_utc provenance",
                evidence={"metadata_keys": sorted(metadata.keys())},
                severity="low",
            )
        ]
    return []


def check_trace_tool_audit(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    for tool in _nodes(genome, "tool_binding"):
        attrs = tool.get("attrs") or {}
        if attrs.get("trace_line") and not attrs.get("allowed_actions"):
            drifts.append(
                format_drift(
                    code="RNT-20",
                    summary=f"trace tool_binding {tool.get('label')} lacks audit/constraints",
                    evidence={"node_id": tool.get("id"), "trace_line": attrs.get("trace_line")},
                    ma13_class="III",
                    severity="high",
                )
            )
    return drifts


def check_model_validation_edges(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    model_ids = {str(n.get("id")) for n in _nodes(genome, "model_call")}
    validated: set[str] = set()
    for edge in genome.get("edges") or []:
        if str(edge.get("type")) == "validates" and str(edge.get("target")) in model_ids:
            validated.add(str(edge.get("target")))
    missing = model_ids - validated
    if len(model_ids) >= 2 and missing:
        drifts.append(
            format_drift(
                code="RNT-22",
                summary="model_call chain missing validates edges on downstream calls",
                evidence={"unvalidated_model_ids": sorted(missing)[:6]},
                ma13_class="II",
                severity="medium",
            )
        )
    return drifts


def check_tool_cost_ceiling(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    tools = _nodes(genome, "tool_binding")
    cost_centers = _nodes(genome, "cost_center")
    if len(tools) >= 2 and not cost_centers:
        return [
            format_drift(
                code="CST-12",
                summary="multiple tool_binding nodes without cost ceiling metadata",
                evidence={"tool_binding_count": len(tools)},
                severity="medium",
            )
        ]
    return []


def check_tool_constraints(genome: Genome, spec: dict[str, Any]) -> list[dict[str, Any]]:
    del spec
    drifts: list[dict[str, Any]] = []
    tools = _nodes(genome, "tool_binding")
    if not tools:
        mcp_hints = [
            n
            for n in genome.get("nodes") or []
            if "mcp" in str(n.get("source_path") or "").lower()
        ]
        if mcp_hints:
            drifts.append(
                format_drift(
                    code="RNT-15",
                    summary="MCP-like paths detected without tool_binding constraint nodes",
                    evidence={"hint_count": len(mcp_hints)},
                    ma13_class="III",
                    severity="high",
                )
            )
    for tool in tools:
        attrs = tool.get("attrs") or {}
        if not attrs.get("allowed_actions"):
            drifts.append(
                format_drift(
                    code="RNT-15",
                    summary=f"tool_binding {tool.get('label')} missing allowed_actions",
                    evidence={"node_id": tool.get("id")},
                    ma13_class="III",
                    severity="high",
                )
            )
    return drifts


_EVALUATORS: dict[str, EvaluatorFn] = {
    "check_decision_owner": check_decision_owner,
    "check_exception_surface": check_exception_surface,
    "check_prompt_governance": check_prompt_governance,
    "check_self_loop_boundary": check_self_loop_boundary,
    "check_output_validation": check_output_validation,
    "check_audit_hooks": check_audit_hooks,
    "check_redundant_model_calls": check_redundant_model_calls,
    "check_cost_center_tagging": check_cost_center_tagging,
    "check_human_control_substitute": check_human_control_substitute,
    "check_hitl_on_high_impact": check_hitl_on_high_impact,
    "check_shadow_workflows": check_shadow_workflows,
    "check_tool_constraints": check_tool_constraints,
    "check_prompt_stage2_fidelity": check_prompt_stage2_fidelity,
    "check_rollback_metadata": check_rollback_metadata,
    "check_extraction_provenance": check_extraction_provenance,
    "check_trace_tool_audit": check_trace_tool_audit,
    "check_model_validation_edges": check_model_validation_edges,
    "check_tool_cost_ceiling": check_tool_cost_ceiling,
}


def evaluate_all(genome: Genome) -> list[dict[str, Any]]:
    catalog = load_invariant_catalog()
    drifts: list[dict[str, Any]] = []
    for item in catalog.get("invariants") or []:
        inv_id = str(item.get("id") or "")
        runner_name = str(item.get("evaluator") or "")
        runner = _EVALUATORS.get(runner_name)
        if runner:
            drifts.extend(runner(genome, item))
    return sorted(drifts, key=lambda d: (str(d.get("code")), str(d.get("drift_summary"))))
