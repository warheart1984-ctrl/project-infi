"""UGR continuity invariant checks for the lawful Nova slice."""

from __future__ import annotations

import hashlib
import json
import os
from typing import TYPE_CHECKING, Any

from nova.exceptions import GovernanceViolationError

if TYPE_CHECKING:
    from nova.lawful_llm import LongScaleGraphStore

INVARIANT_IDS = (
    "ugr.identity_continuity",
    "ugr.authority_continuity",
    "ugr.duality.bidirectional_coherence",
    "ugr.duality.symmetric_constraints",
    "ugr.evidence_integrity",
    "ugr.law_surface_binding",
    "ugr.continuity_unifier",
)


def _status(passed: bool, detail: str) -> dict[str, str]:
    return {"status": "pass" if passed else "fail", "detail": detail}


def evaluate_ugr_invariants(
    *,
    tenant_id: str,
    capability: str,
    prompt: str,
    rsl: dict[str, Any],
    nova_cortex: dict[str, Any],
    api_kernel: dict[str, Any],
    identity: dict[str, Any],
    lsg_store: LongScaleGraphStore | None,
    allowed_capabilities: set[str],
    memory_facts_sha256: str,
    memory_facts_used: list[str],
) -> dict[str, dict[str, str]]:
    """Evaluate the seven UGR continuity invariants for one lawful turn."""
    from nova.lawful_llm import UnifiedLanguage

    results: dict[str, dict[str, str]] = {}

    instance_id = str(identity.get("instance_id") or "")
    results["ugr.identity_continuity"] = _status(
        bool(instance_id),
        f"instance_id={instance_id!r}, tenant={tenant_id!r}",
    )

    cap_ok = capability in allowed_capabilities
    results["ugr.authority_continuity"] = _status(
        cap_ok and str(api_kernel.get("capability") or "") == capability,
        f"capability={capability!r}, allowed={cap_ok}",
    )

    coherence_ok = True
    coherence_detail = "no lsg_store"
    if lsg_store is not None:
        ul_packet = UnifiedLanguage().parse(prompt)
        replay = lsg_store.query(tenant_id=tenant_id, ul_packet=ul_packet)
        replay_facts = list(replay.get("facts_used") or [])
        replay_sha = hashlib.sha256(
            json.dumps(replay_facts, sort_keys=True).encode("utf-8")
        ).hexdigest()
        coherence_ok = replay_sha == memory_facts_sha256
        coherence_detail = f"sha_match={coherence_ok}"
    results["ugr.duality.bidirectional_coherence"] = _status(coherence_ok, coherence_detail)

    law_surface = str(rsl.get("law_surface") or "")
    symmetric_ok = law_surface and law_surface == str(api_kernel.get("law_surface") or "")
    results["ugr.duality.symmetric_constraints"] = _status(
        symmetric_ok,
        f"law_surface={law_surface!r}",
    )

    ul_intent = str((nova_cortex.get("ul") or {}).get("intent") or "")
    needs_evidence = ul_intent in {"explain", "summarize"}
    evidence_ok = bool(memory_facts_used) if needs_evidence else True
    results["ugr.evidence_integrity"] = _status(
        evidence_ok,
        f"intent={ul_intent!r}, facts_used={len(memory_facts_used)}",
    )

    law_ok = str(rsl.get("status") or "") == "SATISFIED" and cap_ok
    results["ugr.law_surface_binding"] = _status(
        law_ok,
        f"rsl_status={rsl.get('status')!r}, law_surface={law_surface!r}",
    )

    all_pass = all(entry["status"] == "pass" for entry in results.values())
    results["ugr.continuity_unifier"] = _status(
        all_pass,
        "all invariants satisfied" if all_pass else "one or more invariants failed",
    )

    return results


def ugr_strict_enabled() -> bool:
    return os.environ.get("NOVA_UGR_STRICT", "").strip().lower() in {"1", "true", "yes"}


def enforce_ugr_invariants(report: dict[str, dict[str, str]]) -> None:
    """Raise GovernanceViolationError when strict mode is on and any invariant fails."""
    if not ugr_strict_enabled():
        return
    failures = [iid for iid, entry in report.items() if entry.get("status") != "pass"]
    if failures:
        raise GovernanceViolationError(
            f"UGR continuity invariant failure: {', '.join(failures)}",
            code="UGR-INVARIANT-FAILURE",
        )
