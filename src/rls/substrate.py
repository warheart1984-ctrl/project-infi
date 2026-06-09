"""RLS evaluation orchestrator."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from src.otem_capability import authority_band, get_otem_capability_level
from src.rls.constitutional import check_constitutional_violations
from src.rls.falsity_registry import FalsityRegistry, check_monotonic_falsity
from src.rls.reasoning_graph import normalize_reasoning_graph
from src.rls.validators import run_test_phase

RLS_MODULE_ID = "aais.rls.substrate"

BAND_TO_MODE = {
    "autonomous": "lightweight",
    "governed": "governed",
    "containment": "paranoid",
    "sovereign": "hyper_strict",
}

STANDING_ORDER = ("denied", "hypothetical", "asserted", "proven")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def rls_mode_for_level(level: int | None = None) -> str:
    resolved = get_otem_capability_level() if level is None else int(level)
    band = authority_band(resolved)
    return BAND_TO_MODE.get(band, "governed")


def _severity_rank(severity: str) -> int:
    return {"info": 0, "warning": 1, "error": 2}.get(str(severity), 1)


def _dedupe_violations(violations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, tuple[str, ...]]] = set()
    out: list[dict[str, Any]] = []
    for v in violations:
        key = (
            str(v.get("code")),
            str(v.get("detail")),
            tuple(v.get("node_ids") or []),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out


def _confidence_band_from_violations(
    verdict: str,
    violations: list[dict[str, Any]],
    *,
    mode: str,
) -> str:
    if verdict == "reject":
        return "denied"
    errors = [v for v in violations if _severity_rank(str(v.get("severity"))) >= 2]
    warnings = [v for v in violations if str(v.get("severity")) == "warning"]
    if verdict == "downgrade" or warnings:
        if mode in ("paranoid", "hyper_strict"):
            return "hypothetical"
        return "asserted"
    if mode == "hyper_strict" and not errors:
        return "proven"
    if mode in ("governed", "paranoid", "hyper_strict"):
        return "asserted"
    return "hypothetical" if warnings else "asserted"


def _verdict_from_violations(
    violations: list[dict[str, Any]],
    *,
    mode: str,
) -> str:
    errors = [v for v in violations if _severity_rank(str(v.get("severity"))) >= 2]
    warnings = [v for v in violations if str(v.get("severity")) == "warning"]

    if errors:
        return "reject"
    if warnings:
        if mode == "lightweight":
            return "downgrade"
        if mode == "governed":
            return "downgrade"
        return "reject"
    return "admit"


def _escalation_blocked(verdict: str, confidence_band: str, mode: str) -> bool:
    if verdict == "reject":
        return True
    if verdict == "downgrade":
        return True
    if mode == "governed" and STANDING_ORDER.index(confidence_band) < STANDING_ORDER.index("asserted"):
        return True
    if mode in ("paranoid", "hyper_strict") and confidence_band != "proven":
        return mode == "hyper_strict" or verdict != "admit"
    return False


def evaluate_reasoning_graph(
    graph: dict[str, Any],
    *,
    otem_level: int | None = None,
    context: dict[str, Any] | None = None,
    registry: FalsityRegistry | None = None,
    record_quarantine: bool = True,
) -> dict[str, Any]:
    """
    Evaluate a ReasoningGraph and return an RLSVerdict.

    Fail-closed: governed+ bands treat evaluation errors as reject.
    """
    _ = context
    resolved_level = get_otem_capability_level() if otem_level is None else int(otem_level)
    mode = rls_mode_for_level(resolved_level)
    reg = registry or FalsityRegistry()

    try:
        normalized = normalize_reasoning_graph(graph)
    except ValueError as exc:
        return {
            "verdict": "reject",
            "confidence_band": "denied",
            "violations": [
                {
                    "code": "orphan_conclusion",
                    "severity": "error",
                    "node_ids": [],
                    "detail": str(exc),
                }
            ],
            "mode": mode,
            "graph_id": str((graph or {}).get("id") or "unknown"),
            "otem_level": resolved_level,
            "quarantine_id": str(uuid.uuid4()),
            "cannot_justify_escalation": True,
            "evaluated_at": _utc_now_iso(),
            "module_id": RLS_MODULE_ID,
        }

    violations: list[dict[str, Any]] = []
    violations.extend(run_test_phase(normalized, mode=mode))
    violations.extend(check_constitutional_violations(normalized))
    violations.extend(check_monotonic_falsity(normalized, reg))
    violations = _dedupe_violations(violations)

    verdict = _verdict_from_violations(violations, mode=mode)
    confidence_band = _confidence_band_from_violations(verdict, violations, mode=mode)

    if mode in ("governed", "paranoid", "hyper_strict") and verdict == "admit":
        if mode == "hyper_strict" and confidence_band != "proven":
            verdict = "reject"
            confidence_band = "denied"
        elif mode == "paranoid" and any(
            v.get("code") in ("speculative_at_ceiling", "missing_evidence") for v in violations
        ):
            verdict = "downgrade"

    quarantine_id = None
    if verdict == "reject":
        quarantine_id = str(uuid.uuid4())
        if record_quarantine:
            from src.rls.quarantine import append_quarantine_event

            append_quarantine_event(
                quarantine_id=quarantine_id,
                graph_id=normalized["id"],
                violations=violations,
                mode=mode,
                otem_level=resolved_level,
            )
        constitutional = [v for v in violations if v.get("code") == "constitutional_conflict"]
        if constitutional:
            conclusion_nodes = [
                n
                for n in normalized.get("nodes") or []
                if str(n.get("id")) == normalized.get("conclusion_id")
            ]
            if conclusion_nodes:
                ctext = str(conclusion_nodes[0].get("text") or "")
                reg.record_falsified(
                    text=ctext,
                    reason="rls_constitutional_reject",
                    graph_id=normalized["id"],
                    invariant_id=str(constitutional[0].get("invariant_id") or ""),
                )

    return {
        "verdict": verdict,
        "confidence_band": confidence_band,
        "violations": violations,
        "mode": mode,
        "graph_id": normalized["id"],
        "otem_level": resolved_level,
        "quarantine_id": quarantine_id,
        "cannot_justify_escalation": _escalation_blocked(verdict, confidence_band, mode),
        "evaluated_at": _utc_now_iso(),
        "module_id": RLS_MODULE_ID,
    }


def evaluate_missing_verdict(otem_level: int | None = None) -> dict[str, Any]:
    """Fail-closed verdict when RLS evaluation was not performed (governed+)."""
    resolved_level = get_otem_capability_level() if otem_level is None else int(otem_level)
    mode = rls_mode_for_level(resolved_level)
    band = authority_band(resolved_level)
    if band == "autonomous":
        return {
            "verdict": "downgrade",
            "confidence_band": "hypothetical",
            "violations": [],
            "mode": mode,
            "graph_id": "missing",
            "otem_level": resolved_level,
            "cannot_justify_escalation": True,
            "evaluated_at": _utc_now_iso(),
            "module_id": RLS_MODULE_ID,
        }
    return {
        "verdict": "reject",
        "confidence_band": "denied",
        "violations": [
            {
                "code": "missing_verdict",
                "severity": "error",
                "node_ids": [],
                "detail": "RLS verdict missing in governed+ band (fail_closed)",
            }
        ],
        "mode": mode,
        "graph_id": "missing",
        "otem_level": resolved_level,
        "quarantine_id": str(uuid.uuid4()),
        "cannot_justify_escalation": True,
        "evaluated_at": _utc_now_iso(),
        "module_id": RLS_MODULE_ID,
    }


def rls_allows_escalation(verdict: dict[str, Any] | None, *, otem_level: int | None = None) -> bool:
    """Whether RLS verdict permits OTEM escalation justification."""
    if not verdict:
        fallback = evaluate_missing_verdict(otem_level)
        return fallback.get("verdict") == "admit" and not fallback.get("cannot_justify_escalation")
    if str(verdict.get("verdict")) == "reject":
        return False
    if verdict.get("cannot_justify_escalation"):
        return False
    mode = str(verdict.get("mode") or rls_mode_for_level(otem_level))
    band = str(verdict.get("confidence_band") or "denied")
    if mode == "lightweight":
        return True
    if mode == "governed":
        return band in ("asserted", "proven") and verdict.get("verdict") == "admit"
    if mode == "paranoid":
        return verdict.get("verdict") == "admit" and band in ("asserted", "proven")
    return verdict.get("verdict") == "admit" and band == "proven"
