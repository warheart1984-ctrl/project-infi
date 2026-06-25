"""JPSS-I + ECK-2 Stewardship Handbook — practical guide for judgment-preserving stewards."""

from __future__ import annotations

import sys
from typing import IO

from constitutional.core.articles import ARTICLE_JPSS_I_REFERENCE, ECK2_REFERENCE
from constitutional.jpss.jpss_i_spec import (
    JPSS_I_ADAPTIVE_CYCLE,
    JPSS_I_ADAPTIVE_REGISTERS,
    JPSS_I_INVARIANT_CHAIN,
    JPSS_I_INVARIANT_DRIFT_CLASSES,
    JPSS_I_INVARIANT_REGISTERS,
)

STEWARDSHIP_HANDBOOK_REFERENCE = "JPSS-I + ECK-2 Stewardship Handbook"

STEWARD_OATH = (
    "I will preserve what must endure.\n"
    "I will adapt what must evolve.\n"
    "I will know the difference."
)

STEWARDSHIP_DEFINITION = (
    "Stewardship is not decision-making.\n"
    "Stewardship is not governance.\n"
    "Stewardship is not alignment.\n\n"
    "Stewardship is: the ability to preserve identity while enabling adaptation."
)

ADAPTIVE_DRIFT_WATCHLIST: tuple[str, ...] = (
    "salience inversion",
    "calibration erosion",
    "perceptual narrowing",
    "outcome misattribution",
    "reflection suppression",
)

INVARIANT_DRIFT_WATCHLIST: tuple[str, ...] = tuple(
    drift.replace("_", " ") for drift in JPSS_I_INVARIANT_DRIFT_CLASSES
)


def format_stewardship_handbook() -> str:
    """Render the full stewardship handbook as steward-facing text."""
    adaptive_cycle = " → ".join(JPSS_I_ADAPTIVE_CYCLE)
    invariant_chain = " → ".join(JPSS_I_INVARIANT_CHAIN)
    adaptive_registers = ", ".join(JPSS_I_ADAPTIVE_REGISTERS)
    invariant_registers = ", ".join(JPSS_I_INVARIANT_REGISTERS)
    adaptive_drift = "\n".join(f"  - {item}" for item in ADAPTIVE_DRIFT_WATCHLIST)
    invariant_drift = "\n".join(f"  - {item}" for item in INVARIANT_DRIFT_WATCHLIST)

    return "\n".join(
        [
            "",
            f"=== {STEWARDSHIP_HANDBOOK_REFERENCE} ===",
            f"Authority: {ARTICLE_JPSS_I_REFERENCE} | {ECK2_REFERENCE}",
            "----------------------------------------",
            "",
            "1. WHAT STEWARDSHIP ACTUALLY IS",
            STEWARDSHIP_DEFINITION,
            "",
            "A steward must know:",
            "  - what must change (adaptive judgment)",
            "  - what must not change (invariant judgment)",
            "This is the core competency.",
            "",
            "2. THE TWO JUDGMENT LAYERS",
            "",
            "A. Adaptive Judgment (JPSS-1)",
            adaptive_cycle,
            "Plastic, responsive, world-driven.",
            "",
            "B. Invariant Judgment (Continuity-1)",
            invariant_chain,
            "Anchored, stable, identity-driven.",
            "",
            "C. Stewardship Layer",
            '  "What must change?"',
            '  "What must remain true?"',
            "",
            "3. THE DUAL PIPELINES OF ECK-2",
            "Formation Pipeline (Forward) — making new judgments.",
            "Reconstruction Pipeline (Reverse) — understanding past judgments.",
            "A steward must be fluent in both.",
            "",
            "4. THE REGISTERS YOU MUST MAINTAIN",
            "",
            "Adaptive Registers:",
            f"  {adaptive_registers}",
            "",
            "Invariant Registers:",
            f"  {invariant_registers}",
            "",
            'These are the "flight recorders" of judgment.',
            "",
            "5. THE DRIFT YOU MUST DETECT",
            "",
            "Adaptive Drift:",
            adaptive_drift,
            "",
            "Invariant Drift:",
            invariant_drift,
            "",
            "A steward must detect both.",
            "",
            "6. THE STEWARD'S OATH (operational)",
            STEWARD_OATH,
            "========================================",
            "",
        ]
    )


def render_stewardship_handbook(*, stream: IO[str] | None = None) -> str:
    text = format_stewardship_handbook()
    out = stream if stream is not None else sys.stdout
    out.write(text)
    if stream is None:
        out.flush()
    return text
