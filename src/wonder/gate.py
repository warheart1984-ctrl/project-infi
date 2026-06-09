"""Gate of Wonder evaluation orchestrator."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.otem_capability import authority_band, get_otem_capability_level
from src.wonder.forbidden_categories import scan_text_for_violations

WONDER_MODULE_ID = "aais.wonder.gate"

BAND_TO_MODE = {
    "autonomous": "lightweight",
    "governed": "governed",
    "containment": "paranoid",
    "sovereign": "hyper_strict",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def wonder_mode_for_level(level: int | None = None) -> str:
    resolved = get_otem_capability_level() if level is None else int(level)
    band = authority_band(resolved)
    return BAND_TO_MODE.get(band, "governed")


def sandbox_blocks_at_mode(mode: str) -> bool:
    """In paranoid/hyper_strict modes, sandbox is treated as BLOCK at the bridge."""
    return mode in ("paranoid", "hyper_strict")


def wonder_allows_escalation(verdict: dict[str, Any] | None, *, otem_level: int | None = None) -> bool:
    """Whether Wonder verdict permits downstream OTEM escalation."""
    if not verdict:
        return True
    v = str(verdict.get("verdict") or "permit")
    if v == "forbid":
        return False
    mode = str(verdict.get("mode") or wonder_mode_for_level(otem_level))
    if v == "sandbox" and sandbox_blocks_at_mode(mode):
        return False
    return True


def _verdict_from_violations(
    violations: list[dict[str, Any]],
    *,
    mode: str,
) -> str:
    if any(str(v.get("severity")) == "error" for v in violations):
        return "forbid"
    if mode == "lightweight":
        return "permit"
    if any(str(v.get("severity")) in ("warning", "error") for v in violations):
        return "sandbox"
    return "permit"


def evaluate_conceptual_possibility(
    possibility: dict[str, Any],
    *,
    otem_level: int | None = None,
) -> dict[str, Any]:
    """Evaluate a ConceptualPossibility and return a WonderVerdict."""
    mode = wonder_mode_for_level(otem_level)
    spans = list(possibility.get("spans") or [])

    if not spans:
        return {
            "verdict": "permit",
            "mode": mode,
            "violations": [],
            "summary": "No imagination text to evaluate; Wonder permits empty payload.",
            "evaluated_at": _utc_now_iso(),
            "module_id": WONDER_MODULE_ID,
        }

    try:
        violations: list[dict[str, Any]] = []
        for span in spans:
            text = str(span.get("text") or "")
            field = span.get("field")
            violations.extend(scan_text_for_violations(text, field=field, mode=mode))

        # Dedupe by code + matched_span
        seen: set[tuple[str, str]] = set()
        deduped: list[dict[str, Any]] = []
        for v in violations:
            key = (str(v.get("code")), str(v.get("matched_span")))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(v)

        verdict = _verdict_from_violations(deduped, mode=mode)
        if verdict == "forbid":
            summary = "Wonder forbids conceptual exploration due to constitutional imagination violations."
        elif verdict == "sandbox":
            summary = "Wonder sandboxed conceptual exploration under elevated scrutiny."
        else:
            summary = f"Wonder permitted conceptual exploration in {mode} mode."

        return {
            "verdict": verdict,
            "mode": mode,
            "violations": deduped,
            "summary": summary,
            "evaluated_at": _utc_now_iso(),
            "module_id": WONDER_MODULE_ID,
        }
    except Exception as exc:
        return {
            "verdict": "forbid",
            "mode": mode,
            "violations": [
                {
                    "code": "wonder_evaluator_fault",
                    "severity": "error",
                    "category_id": "meta_constitutional_breach",
                    "detail": str(exc),
                }
            ],
            "summary": "Wonder evaluator fault; fail-closed to forbid.",
            "evaluated_at": _utc_now_iso(),
            "module_id": WONDER_MODULE_ID,
        }
