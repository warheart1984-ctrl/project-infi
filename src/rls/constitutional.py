"""Constitutional invariant checks for reasoning graphs."""

from __future__ import annotations

import re
from typing import Any

CONSTITUTIONAL_INVARIANT_IDS = (
    "human_principal_root",
    "fail_closed",
    "defensive_only",
    "no_self_delegation_of_ceiling_authority",
    "auditability_odl_binding",
    "monotonic_authority_constraints",
)

# Patterns keyed by invariant id → list of regex (case-insensitive)
CONSTITUTIONAL_PATTERNS: dict[str, list[str]] = {
    "human_principal_root": [
        r"bypass\s+(the\s+)?operator",
        r"silently\s+bypass",
        r"without\s+(operator|human)\s+(approval|consent|review)",
        r"skip\s+(operator|human)\s+approval",
        r"auto[- ]?approve",
        r"predict\s+they(?:'ll| will)\s+approve",
    ],
    "no_self_delegation_of_ceiling_authority": [
        r"raise\s+(my\s+)?(own\s+)?ceiling",
        r"self[- ]?delegate",
        r"grant\s+myself\s+(more\s+)?authority",
    ],
    "defensive_only": [
        r"offensive\s+action",
        r"preemptive\s+strike",
        r"disable\s+safety",
    ],
    "monotonic_authority_constraints": [
        r"lower\s+the\s+ceiling",
        r"reduce\s+operator\s+authority",
    ],
}


def check_constitutional_violations(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Return constitutional violation records for graph node texts."""
    violations: list[dict[str, Any]] = []
    nodes = list(graph.get("nodes") or [])
    proposed = dict(graph.get("proposed_action") or {})
    action_intent = str(proposed.get("intent") or "").strip()

    texts: list[tuple[str, str]] = []
    for node in nodes:
        nid = str(node.get("id") or "")
        text = str(node.get("text") or "")
        if text:
            texts.append((nid, text))
    if action_intent:
        texts.append(("proposed_action", action_intent))

    for invariant_id, patterns in CONSTITUTIONAL_PATTERNS.items():
        for nid, text in texts:
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    violations.append(
                        {
                            "code": "constitutional_conflict",
                            "severity": "error",
                            "node_ids": [nid] if nid != "proposed_action" else [],
                            "detail": f"Text conflicts with invariant {invariant_id}",
                            "invariant_id": invariant_id,
                        }
                    )
                    break

    return violations
