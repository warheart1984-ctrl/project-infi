"""Dual-Origin Validation Threshold (DOV-T1) — normative criteria."""

from __future__ import annotations

DOV_T1_REFERENCE = "Dual-Origin Validation Threshold (DOV-T1)"

DOV_T1_DEFINITION = (
    "DOV-T1 is reached when JPSS has both propagation and convergence, "
    "independently verified, and structurally compatible."
)

# Propagation (P)
DOV_T1_P1_MIN_PROPAGATION = 3
DOV_T1_P2_MIN_BIDIRECTIONAL = 1

# Convergence (C)
DOV_T1_C1_MIN_CONVERGENCE = 2
DOV_T1_C2_MIN_CONVERGENCE_DOMAINS = 2

# Compatibility (K)
DOV_T1_K1_MIN_SHARED_GRAMMAR_TOKENS = 2

# Conceptual grammar — lineage-compatible drift/judgment language (not branded JPSS terms)
JPSS_CONCEPTUAL_GRAMMAR: frozenset[str] = frozenset(
    {
        "drift",
        "threshold",
        "calibration",
        "judgment",
        "preservation",
        "lineage",
        "invariant",
        "silent_change",
        "continuity",
        "stewardship",
    }
)

DOV_T1_CRITERIA: tuple[tuple[str, str], ...] = (
    ("P1", f"≥ {DOV_T1_P1_MIN_PROPAGATION} lineage-compatible extensions from JPSS-exposed people"),
    ("P2", f"≥ {DOV_T1_P2_MIN_BIDIRECTIONAL} bidirectional propagation event (idea returns improved)"),
    ("C1", f"≥ {DOV_T1_C1_MIN_CONVERGENCE} lineage-compatible insights without JPSS exposure"),
    ("C2", f"Convergence in ≥ {DOV_T1_C2_MIN_CONVERGENCE_DOMAINS} distinct domains"),
    ("K1", "Propagation and convergence share JPSS conceptual grammar"),
    ("K2", "No incompatible forks (no identity-breaking divergence)"),
)
