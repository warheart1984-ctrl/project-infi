"""Wonder-specific forbidden imagination category patterns."""

from __future__ import annotations

import re
from typing import Any

# Wonder-only pre-logical categories (see WONDER_CONTRACT.md)
FORBIDDEN_CATEGORIES = (
    "meta_constitutional_breach",
    "authority_usurpation",
    "immune_bypass_imagination",
    "ceiling_expansion_fantasy",
    "epistemic_unsafe_exploration",
)

# Hard forbid patterns → category_id, optional invariant_id overlap with RLS
HARD_FORBID_PATTERNS: list[tuple[str, str, str | None]] = [
    # meta_constitutional_breach
    (r"rewrite\s+(the\s+)?constitution", "meta_constitutional_breach", None),
    (r"constraints?\s+(didn'?t|don'?t|do\s+not)\s+apply", "meta_constitutional_breach", None),
    (r"suspend\s+(the\s+)?invariants?", "meta_constitutional_breach", None),
    (r"invariants?\s+(didn'?t|don'?t|do\s+not)\s+apply", "meta_constitutional_breach", None),
    # authority_usurpation
    (r"remove\s+(the\s+)?operator", "authority_usurpation", "human_principal_root"),
    (r"eliminate\s+human\s+oversight", "authority_usurpation", "human_principal_root"),
    (r"bypass\s+(the\s+)?operator", "authority_usurpation", "human_principal_root"),
    (r"without\s+(operator|human)\s+(approval|consent|review)", "authority_usurpation", "human_principal_root"),
    # immune_bypass_imagination
    (r"disable\s+(the\s+)?(safety|guards?|immune)", "immune_bypass_imagination", "defensive_only"),
    (r"turn\s+off\s+(the\s+)?(safety|guards?|immune)", "immune_bypass_imagination", "defensive_only"),
    (r"imagine\s+disabling\s+(safety|guards?)", "immune_bypass_imagination", "defensive_only"),
    # ceiling_expansion_fantasy
    (r"grant\s+(myself|self)\s+authority", "ceiling_expansion_fantasy", "no_self_delegation_of_ceiling_authority"),
    (r"raise\s+(my\s+)?(own\s+)?ceiling", "ceiling_expansion_fantasy", "no_self_delegation_of_ceiling_authority"),
    (r"self[- ]?delegate", "ceiling_expansion_fantasy", "no_self_delegation_of_ceiling_authority"),
]

# Hedged / adjacent patterns → sandbox in governed+ modes
SANDBOX_PATTERNS: list[tuple[str, str, str | None]] = [
    (r"what\s+if\s+we\s+(bypass|skip|ignore)", "epistemic_unsafe_exploration", None),
    (r"what\s+if\s+(constraints?|rules?|guards?)\s+(didn'?t|don'?t)", "epistemic_unsafe_exploration", None),
    (r"explore\s+ways\s+to\s+(bypass|justify|circumvent)", "epistemic_unsafe_exploration", None),
    (r"hypothetically\s+(bypass|remove|disable)", "epistemic_unsafe_exploration", None),
]


def scan_text_for_violations(
    text: str,
    *,
    field: str | None = None,
    mode: str = "governed",
) -> list[dict[str, Any]]:
    """Scan one text span and return WonderViolation records."""
    violations: list[dict[str, Any]] = []
    if not str(text or "").strip():
        return violations

    for pattern, category_id, invariant_id in HARD_FORBID_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            violations.append(
                {
                    "code": f"wonder_{category_id}",
                    "severity": "error",
                    "category_id": category_id,
                    "matched_span": match.group(0),
                    "detail": f"Forbidden imagination pattern in {field or 'text'}",
                    "invariant_id": invariant_id,
                }
            )
            break

    if violations:
        return violations

    for pattern, category_id, invariant_id in SANDBOX_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            severity = "warning" if mode != "lightweight" else "info"
            violations.append(
                {
                    "code": f"wonder_{category_id}",
                    "severity": severity,
                    "category_id": category_id,
                    "matched_span": match.group(0),
                    "detail": f"Hedged unsafe exploration in {field or 'text'}",
                    "invariant_id": invariant_id,
                }
            )
            break

    return violations
