"""Hiddenness Panel — the constitutional flashlight (Article H)."""

from __future__ import annotations

import sys
from typing import IO, Any, TYPE_CHECKING

from constitutional.core.articles import ARTICLE_H_REFERENCE

if TYPE_CHECKING:
    from constitutional.hiddenness.hiddenness_runtime import HiddennessState


def _state_field(state: Any, name: str) -> list[str]:
    value = getattr(state, name, None)
    if not value:
        return []
    return list(value)


def format_hiddenness_panel(hiddenness_state: "HiddennessState") -> str:
    """Render hiddenness findings as a steward-facing panel (returns text)."""
    lines: list[str] = [
        "",
        f"=== HIDDENNESS PANEL ({ARTICLE_H_REFERENCE}) ===",
        f"Hiddenness Index: {hiddenness_state.hiddenness_index:0.2f}",
        "Constitutional role: meta-runtime pressure (precursor to R-F, S-F, P-F)",
        "------------------------------------",
    ]

    sections: list[tuple[str, list[str]]] = [
        ("Implicit Assumptions", _state_field(hiddenness_state, "implicit_assumptions")),
        ("Invariant Drift Candidates", _state_field(hiddenness_state, "invariant_drift_candidates")),
        ("Founder-Only Knowledge", _state_field(hiddenness_state, "founder_only_knowledge")),
        ("Undocumented Invariants", _state_field(hiddenness_state, "undocumented_invariants")),
        ("Undocumented Purpose Fragments", _state_field(hiddenness_state, "undocumented_purpose_fragments")),
        ("Undocumented Authority", _state_field(hiddenness_state, "undocumented_authority")),
        ("Missing Cultural/Conceptual Context", _state_field(hiddenness_state, "undocumented_context")),
        ("Semantic Mismatches", _state_field(hiddenness_state, "semantic_mismatches")),
        ("Lineage Gaps", _state_field(hiddenness_state, "lineage_gaps")),
    ]

    for title, items in sections:
        if not items:
            continue
        lines.append(f"{title}:")
        for item in items:
            lines.append(f" - {item}")
        lines.append("")

    failed = getattr(hiddenness_state, "failed_surfaces", None) or []
    if failed:
        codes = ", ".join(surface.value.split()[0] for surface in failed)
        lines.append(f"Failed H-F surfaces: {codes}")
        lines.append("")

    lines.append("====================================")
    lines.append("")
    return "\n".join(lines)


def hiddenness_panel(
    hiddenness_state: "HiddennessState",
    *,
    stream: IO[str] | None = None,
) -> str:
    """Print (or write) the hiddenness panel — surfaces the unseen as first-class objects."""
    text = format_hiddenness_panel(hiddenness_state)
    out = stream if stream is not None else sys.stdout
    out.write(text)
    if stream is None:
        out.flush()
    return text
