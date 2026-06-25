"""Stewardship Legitimacy Protocol v1.0 — canonical steward-facing specification text."""

from __future__ import annotations

import sys
from typing import IO

from constitutional.legitimacy.spec import (
    CONSTITUTIONAL_JUDGMENT_DEFINITION,
    CONSTITUTIONAL_LEGITIMACY_DEFINITION,
    JUDGMENT_LAYER_DESCRIPTIONS,
    JUDGMENT_STACK_LAYERS,
    LEGITIMACY_CAPTURE_VECTORS,
    LEGITIMACY_CRITERIA,
    LEGITIMACY_CRITERION_RULE,
    LEGITIMACY_DRIFT_CLASSES,
    LEGITIMACY_PROCESS_DESCRIPTIONS,
    LEGITIMACY_PROCESS_PHASES,
    LEGITIMACY_PURPOSE,
    LEGITIMACY_RECEIPT_TYPES,
    LEGITIMACY_REFERENCE,
    LEGITIMACY_STABILITY_REQUIREMENTS,
    STEWARDSHIP_LEGITIMACY_DEFINITION,
    STEWARDSHIP_LEGITIMACY_PROBLEM,
)


def format_stewardship_legitimacy_protocol_v1() -> str:
    """Render the full Protocol v1.0 specification as steward-facing text."""
    layers = "\n".join(
        f"  {layer}: {JUDGMENT_LAYER_DESCRIPTIONS[layer]}" for layer in JUDGMENT_STACK_LAYERS
    )
    criteria = "\n".join(f"  1.{idx} {key}: {desc}" for idx, (key, desc) in enumerate(LEGITIMACY_CRITERIA, 1))
    phases = "\n".join(
        f"  Phase {idx} — {phase}: {LEGITIMACY_PROCESS_DESCRIPTIONS[phase]}"
        for idx, phase in enumerate(LEGITIMACY_PROCESS_PHASES, 1)
    )
    receipts = "\n".join(f"  - {receipt_type}" for receipt_type in LEGITIMACY_RECEIPT_TYPES)
    drift = "\n".join(f"  4.{idx} {drift_class}" for idx, drift_class in enumerate(LEGITIMACY_DRIFT_CLASSES, 1))
    stability = "\n".join(f"  - {req.replace('_', ' ')}" for req in LEGITIMACY_STABILITY_REQUIREMENTS)
    capture = "\n".join(f"  - {vector.replace('_', ' ')}" for vector in LEGITIMACY_CAPTURE_VECTORS)

    return "\n".join(
        [
            "",
            f"=== {LEGITIMACY_REFERENCE} ===",
            "Authority grounded in reconstruction, not position",
            "========================================",
            "",
            "0. PURPOSE",
            LEGITIMACY_PURPOSE,
            "",
            STEWARDSHIP_LEGITIMACY_DEFINITION,
            "",
            "Judgment stack:",
            layers,
            "",
            "Constitutional Judgment:", CONSTITUTIONAL_JUDGMENT_DEFINITION,
            "Constitutional Legitimacy:", CONSTITUTIONAL_LEGITIMACY_DEFINITION,
            "",
            "1. LEGITIMACY CRITERIA",
            "A steward is eligible only if they can publicly demonstrate:",
            criteria,
            "",
            LEGITIMACY_CRITERION_RULE,
            "",
            "2. LEGITIMACY PROCESS",
            phases,
            "",
            "3. LEGITIMACY RECEIPTS",
            receipts,
            "",
            "4. LEGITIMACY DRIFT MODEL",
            drift,
            "",
            "5. LEGITIMACY STABILITY REQUIREMENTS",
            stability,
            "",
            "6. REJECTED CAPTURE VECTORS",
            capture,
            "",
            "7. THE STEWARDSHIP LEGITIMACY PROBLEM",
            STEWARDSHIP_LEGITIMACY_PROBLEM,
            "",
            "Answer: demonstrated, reconstructable stewardship competence through a",
            "transparent, repeatable protocol subject to JPSS — not title, vote, or founder.",
            "========================================",
            "",
        ]
    )


def render_stewardship_legitimacy_protocol_v1(*, stream: IO[str] | None = None) -> str:
    text = format_stewardship_legitimacy_protocol_v1()
    out = stream if stream is not None else sys.stdout
    out.write(text)
    if stream is None:
        out.flush()
    return text
