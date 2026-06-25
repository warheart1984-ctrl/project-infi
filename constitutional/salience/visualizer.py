"""Perceptual Map Visualizer — replay salience frames over time."""

from __future__ import annotations

import sys
from typing import IO

from constitutional.salience.ledger import SalienceLedger


def format_perceptual_map(
    salience_ledger: SalienceLedger,
    *,
    artifact_id: str | None = None,
) -> str:
    lines: list[str] = ["", "=== PERCEPTUAL MAP VISUALIZER ==="]

    entries = [
        entry
        for entry in salience_ledger.entries
        if artifact_id is None or entry.artifact_id == artifact_id
    ]
    if not entries:
        lines.extend(["No salience entries found.", "====================================", ""])
        return "\n".join(lines)

    for entry in sorted(entries, key=lambda item: item.timestamp):
        lines.append(f"\n--- Decision {entry.decision_id} @ {entry.timestamp.isoformat()} ---")
        lines.append(f"Artifact: {entry.artifact_id}")
        lines.append(f"Primary Signals: {entry.primary_signals}")
        lines.append(f"Secondary Signals: {entry.secondary_signals}")
        lines.append(f"Ignored Signals: {entry.ignored_signals}")
        lines.append(f"Risk Salience: {entry.risk_salience}")
        lines.append(f"Deprioritized Risks: {entry.deprioritized_risks}")
        lines.append(f"Attention Triggers: {entry.attention_triggers}")
        lines.append(f"Attention Suppressors: {entry.attention_suppressors}")
        lines.append(f"Steward: {entry.steward_id}")
        if entry.notes:
            lines.append(f"Notes: {entry.notes}")

    lines.extend(["", "====================================", ""])
    return "\n".join(lines)


def perceptual_map_visualizer(
    salience_ledger: SalienceLedger,
    *,
    artifact_id: str | None = None,
    stream: IO[str] | None = None,
) -> str:
    text = format_perceptual_map(salience_ledger, artifact_id=artifact_id)
    out = stream if stream is not None else sys.stdout
    out.write(text)
    if stream is None:
        out.flush()
    return text
