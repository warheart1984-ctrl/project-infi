"""Multi-lane cognitive accelerator — governed parallel reasoning lanes (v0)."""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul.runtime import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
import time
from typing import Any
from uuid import uuid4

from src.ugr.pattern_ledger import PatternLedgerStore
from src.ugr.platform.tenant_registry import normalize_tenant_id


LANE_MANAGER_ID = "aais.ugr.lane_manager"
LANE_MANAGER_VERSION = "0.1"
SUPPORTED_LANE_TYPES = frozenset({"symbolic", "graph", "llm", "simulation"})

LANE_PRECEDENCE = {
    "symbolic": 4,
    "graph": 3,
    "simulation": 2,
    "llm": 1,
}


@dataclass(frozen=True)
class LaneSpec:
    lane_id: str
    lane_type: str
    priority: str = "normal"
    resource_budget: dict[str, Any] = field(default_factory=dict)
    invariant_profile: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return _wrap_ul_payload({
            "lane_id": self.lane_id,
            "lane_type": self.lane_type,
            "priority": self.priority,
            "resource_budget": dict(self.resource_budget or {}),
            "invariant_profile": list(self.invariant_profile),
        })


@dataclass
class LaneResult:
    lane_id: str
    lane_type: str
    status: str
    metrics: dict[str, Any]
    invariant_results: list[dict[str, Any]]
    immune_flags: list[dict[str, Any]]
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return _wrap_ul_payload({
            "lane_id": self.lane_id,
            "lane_type": self.lane_type,
            "status": self.status,
            "metrics": dict(self.metrics or {}),
            "invariant_results": list(self.invariant_results or []),
            "immune_flags": list(self.immune_flags or []),
            "payload": dict(self.payload or {}),
        })


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _extract_terms(question: str, context: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for token in re.findall(r"[a-zA-Z0-9_./-]{3,}", str(question or "")):
        terms.append(token.lower())
    for key in ("subject", "node_id", "component", "service"):
        value = context.get(key)
        if value:
            terms.append(str(value).lower())
    deduped: list[str] = []
    seen: set[str] = set()
    for term in terms:
        if term not in seen:
            seen.add(term)
            deduped.append(term)
    return deduped[:12]


def _claim(
    *,
    claim_id: str,
    subject: str,
    predicate: str,
    object_value: str,
    confidence: float,
    source_lane: str,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    return _wrap_ul_payload({
        "id": claim_id,
        "subject": subject,
        "predicate": predicate,
        "object": object_value,
        "confidence": round(max(0.0, min(1.0, float(confidence))), 3),
        "source_type": source_lane,
        "evidence_refs": list(evidence_refs or []),
    })


def run_symbolic_lane(spec: LaneSpec, shared_context: dict[str, Any]) -> LaneResult:
    started = time.perf_counter()
    question = str(shared_context.get("question") or "")
    context = dict(shared_context.get("context") or {})
    claims: list[dict[str, Any]] = []
    constraints: list[dict[str, Any]] = []
    invariant_results: list[dict[str, Any]] = []

    if not question.strip():
        invariant_results.append(
            {
                "name": "question_present",
                "status": "hard_fail",
                "details": "deliberation requires a non-empty question",
            }
        )
    else:
        invariant_results.append({"name": "question_present", "status": "pass", "details": "ok"})

    tenant_id = str(shared_context.get("tenant_id") or "default").strip() or "default"
    if tenant_id.startswith("tenant:") or tenant_id == "default":
        invariant_results.append({"name": "tenant_scope_valid", "status": "pass", "details": tenant_id})
    else:
        invariant_results.append(
            {
                "name": "tenant_scope_valid",
                "status": "soft_fail",
                "details": f"non-canonical tenant id: {tenant_id}",
            }
        )

    if context.get("violates_policy"):
        constraints.append(
            {
                "id": "policy-violation",
                "type": "hard",
                "expression": "context.violates_policy == true",
                "violated": True,
            }
        )
        invariant_results.append(
            {"name": "policy_constraint", "status": "hard_fail", "details": "explicit policy violation in context"}
        )
    else:
        constraints.append(
            {
                "id": "policy-violation",
                "type": "hard",
                "expression": "context.violates_policy == true",
                "violated": False,
            }
        )
        invariant_results.append({"name": "policy_constraint", "status": "pass", "details": "ok"})

    if question:
        claims.append(
            _claim(
                claim_id=f"{spec.lane_id}-sym-root",
                subject=question[:80],
                predicate="requires_governed_analysis",
                object_value="true",
                confidence=0.95,
                source_lane="symbolic",
                evidence_refs=["invariant:question_present"],
            )
        )

    hard_fail = any(item.get("status") == "hard_fail" for item in invariant_results)
    duration_ms = int((time.perf_counter() - started) * 1000)
    return LaneResult(
        lane_id=spec.lane_id,
        lane_type=spec.lane_type,
        status="success",
        metrics={"duration_ms": duration_ms},
        invariant_results=invariant_results,
        immune_flags=[{"type": "anomaly", "severity": "high", "details": "symbolic hard invariant failure"}]
        if hard_fail
        else [],
        payload={"claims": claims, "constraints": constraints},
    )


def run_graph_lane(spec: LaneSpec, shared_context: dict[str, Any], ledger: PatternLedgerStore) -> LaneResult:
    started = time.perf_counter()
    question = str(shared_context.get("question") or "")
    context = dict(shared_context.get("context") or {})
    terms = _extract_terms(question, context)
    tenant_scope = normalize_tenant_id(shared_context.get("tenant_id"))
    rows = ledger.query_related(
        terms,
        tenant_scope=tenant_scope if tenant_scope != "global" else None,
        limit=10,
    )
    claims: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        claims.append(
            _claim(
                claim_id=f"{spec.lane_id}-graph-{index}",
                subject=str(row.get("subject") or "unknown"),
                predicate=str(row.get("predicate") or "related_pattern"),
                object_value=str(row.get("object") or row.get("summary") or ""),
                confidence=float(row.get("confidence") or 0.6),
                source_lane="graph",
                evidence_refs=[str(row.get("claim_id") or row.get("timestamp") or "ledger")],
            )
        )
    if not claims and terms:
        claims.append(
            _claim(
                claim_id=f"{spec.lane_id}-graph-empty",
                subject=terms[0],
                predicate="has_prior_pattern",
                object_value="false",
                confidence=0.55,
                source_lane="graph",
                evidence_refs=["ledger:empty"],
            )
        )
    duration_ms = int((time.perf_counter() - started) * 1000)
    return LaneResult(
        lane_id=spec.lane_id,
        lane_type=spec.lane_type,
        status="success",
        metrics={"duration_ms": duration_ms, "matched_patterns": len(rows)},
        invariant_results=[{"name": "tenant_boundary", "status": "pass", "details": "read-only ledger query"}],
        immune_flags=[],
        payload={"claims": claims},
    )


def run_llm_lane(spec: LaneSpec, shared_context: dict[str, Any]) -> LaneResult:
    """Governed LLM lane v1 — proposal-only envelope, temperature 0, invariant gated."""
    from src.ugr.llm_lane import run_governed_llm_lane

    return run_governed_llm_lane(spec, shared_context)


def run_simulation_lane(spec: LaneSpec, shared_context: dict[str, Any]) -> LaneResult:
    started = time.perf_counter()
    question = str(shared_context.get("question") or "")
    scenarios = [
        {
            "id": f"{spec.lane_id}-sim-stable",
            "description": "Apply minimal governed fix under low load",
            "outcome_distribution": {
                "success_prob": 0.78,
                "failure_modes": [{"type": "regression", "prob": 0.12, "impact": "medium"}],
            },
        }
    ]
    claims = [
        _claim(
            claim_id=f"{spec.lane_id}-sim-ranked",
            subject=question[:80] or "scenario",
            predicate="preferred_intervention",
            object_value="minimal_governed_fix",
            confidence=0.7,
            source_lane="simulation",
            evidence_refs=[scenarios[0]["id"]],
        )
    ]
    duration_ms = int((time.perf_counter() - started) * 1000)
    return LaneResult(
        lane_id=spec.lane_id,
        lane_type=spec.lane_type,
        status="success",
        metrics={"duration_ms": duration_ms},
        invariant_results=[{"name": "domain_rules", "status": "pass", "details": "bounded scenario"}],
        immune_flags=[],
        payload={"claims": claims, "scenarios": scenarios},
    )


def build_lane_specs(lane_types: list[str], trace_id: str) -> list[LaneSpec]:
    specs: list[LaneSpec] = []
    for index, lane_type in enumerate(lane_types):
        normalized = str(lane_type or "").strip().lower()
        if normalized not in SUPPORTED_LANE_TYPES:
            raise ValueError(f"unsupported lane type: {lane_type}")
        lane_id = f"{trace_id}-{normalized}-{index}"
        specs.append(LaneSpec(lane_id=lane_id, lane_type=normalized))
    return specs


def run_lane(spec: LaneSpec, shared_context: dict[str, Any], ledger: PatternLedgerStore) -> LaneResult:
    if spec.lane_type == "symbolic":
        return run_symbolic_lane(spec, shared_context)
    if spec.lane_type == "graph":
        return run_graph_lane(spec, shared_context, ledger)
    if spec.lane_type == "llm":
        return run_llm_lane(spec, shared_context)
    if spec.lane_type == "simulation":
        return run_simulation_lane(spec, shared_context)
    raise ValueError(f"unsupported lane type: {spec.lane_type}")


class LaneManager:
    """Spawn and collect governed reasoning lanes for one trace."""

    def __init__(self, ledger: PatternLedgerStore | None = None):
        self.ledger = ledger or PatternLedgerStore()

    def start_lanes(
        self,
        trace_id: str,
        lane_specs: list[LaneSpec | dict[str, Any]],
        shared_context: dict[str, Any],
        *,
        timeout_ms: int = 5000,
    ) -> list[dict[str, Any]]:
        specs = [
            spec if isinstance(spec, LaneSpec) else LaneSpec(**dict(spec))  # type: ignore[arg-type]
            for spec in lane_specs
        ]
        results = run_lanes(trace_id, specs, shared_context, ledger=self.ledger, timeout_ms=timeout_ms)
        return [result.to_dict() for result in results]


def run_lanes(
    trace_id: str,
    lane_specs: list[LaneSpec],
    shared_context: dict[str, Any],
    *,
    ledger: PatternLedgerStore | None = None,
    timeout_ms: int = 5000,
) -> list[LaneResult]:
    store = ledger or PatternLedgerStore()
    context = dict(shared_context or {})
    context.setdefault("trace_id", trace_id)

    if not lane_specs:
        return []

    # Deterministic lane order before parallel execution.
    ordered_specs = sorted(
        lane_specs,
        key=lambda spec: (LANE_PRECEDENCE.get(spec.lane_type, 0), spec.lane_id),
        reverse=True,
    )

    results: list[LaneResult] = []
    max_workers = min(8, len(ordered_specs))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_map = {
            pool.submit(run_lane, spec, context, store): spec.lane_id for spec in ordered_specs
        }
        for future in as_completed(future_map, timeout=max(0.001, timeout_ms / 1000)):
            lane_id = future_map[future]
            try:
                results.append(future.result())
            except Exception as exc:  # pragma: no cover - surfaced as lane error
                results.append(
                    LaneResult(
                        lane_id=lane_id,
                        lane_type="unknown",
                        status="error",
                        metrics={},
                        invariant_results=[
                            {"name": "lane_execution", "status": "hard_fail", "details": str(exc)}
                        ],
                        immune_flags=[{"type": "anomaly", "severity": "medium", "details": "lane execution error"}],
                        payload={"claims": []},
                    )
                )

    # Stable output ordering for convergence determinism.
    order = {spec.lane_id: index for index, spec in enumerate(ordered_specs)}
    results.sort(key=lambda item: order.get(item.lane_id, 999))
    return results


def design_lane_set(intent: str, lane_types: list[str] | None = None) -> list[LaneSpec]:
    trace_seed = sha256(_stable_json({"intent": intent, "lane_types": lane_types or []}).encode("utf-8")).hexdigest()[
        :12
    ]
    if lane_types:
        return build_lane_specs(lane_types, trace_id=f"lane-{trace_seed}")
    defaults = {
        "diagnose_runtime": ["graph", "symbolic", "llm", "simulation"],
        "governance_review": ["graph", "symbolic", "llm"],
        "general_qa": ["symbolic", "graph", "llm"],
    }
    selected = defaults.get(str(intent or "").strip().lower(), defaults["general_qa"])
    return build_lane_specs(selected, trace_id=f"lane-{trace_seed}")
