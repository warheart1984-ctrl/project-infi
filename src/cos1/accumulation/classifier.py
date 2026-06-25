"""ADF-1 accumulation classifier — maps event properties to A1–A4 signatures."""

from __future__ import annotations

from src.cos1.accumulation.ae_json_schema import AccumulationFields, AccumulationSignature


def classify_accumulation(fields: AccumulationFields) -> AccumulationSignature:
    """
    Classify accumulation signature (ADF-1).

    Priority: A3 (integrative) > A2 (structural) > A1 (explanatory) > A4 (generational).
    A4 applies when the event builds on prior events without higher-order signatures.
    """
    if fields.integrative_synthesis:
        return "A3"
    if fields.structural_deepening:
        return "A2"
    if fields.strengthened_explanation:
        return "A1"
    if fields.builds_on_event_ids:
        return "A4"
    return "NONE"
