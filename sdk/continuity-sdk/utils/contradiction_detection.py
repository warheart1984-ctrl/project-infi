"""CRC-3 contradiction detection hook for SDK failure demos."""

from __future__ import annotations

from typing import Any


def detect_contradictions(
    evidence: dict[str, Any],
    state: dict[str, Any],
    prior_decisions: list[dict[str, Any]],
) -> list[str]:
    contradictions: list[str] = []
    expected = state.get("expected")
    observed = evidence.get("observed")
    if expected is not None and observed is not None and expected != observed:
        contradictions.append(f"evidence_vs_state:{expected}!={observed}")
    for decision in prior_decisions:
        if decision.get("commits_to") and decision["commits_to"] != observed:
            contradictions.append(f"prior_decision_{decision.get('id', '?')}_conflict")
    return contradictions
