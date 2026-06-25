"""Salience Panel — perceptual cockpit for Tier 0/1 artifacts (Article Q-6)."""

from __future__ import annotations

import sys
from typing import IO

from constitutional.core.articles import ARTICLE_Q6_REFERENCE
from constitutional.salience.continuity_runtime import SalienceContinuityState, SalienceFailure
from constitutional.salience.ledger import SalienceLedger
from constitutional.salience.perceptual_drift import PerceptualDriftState
from constitutional.stewardship.artifact_index import ArtifactIndex, default_artifact_index


def format_salience_panel(
    salience_ledger: SalienceLedger,
    salience_cont_state: SalienceContinuityState | None,
    perceptual_drift_state: PerceptualDriftState | None,
    *,
    artifact_index: ArtifactIndex | None = None,
) -> str:
    index = artifact_index or default_artifact_index()
    lines: list[str] = [
        "",
        f"=== SALIENCE PANEL ({ARTICLE_Q6_REFERENCE}) ===",
        "Tier 0/1 artifacts — perceptual maps",
        "------------------------------------",
    ]

    entries_by_artifact: dict[str, list] = {}
    for entry in salience_ledger.entries:
        if entry.artifact_id:
            entries_by_artifact.setdefault(entry.artifact_id, []).append(entry)

    for artifact in index.tier_0_and_1():
        lines.append(f"\nArtifact: {artifact.id}")
        lines.append(f"  Tier: {artifact.significance_tier} ({artifact.tier_label})")

        if artifact.id not in entries_by_artifact:
            lines.append(f"  Salience: NO RECORD ({SalienceFailure.SALIENCE_LOSS.value})")
            continue

        latest = sorted(entries_by_artifact[artifact.id], key=lambda entry: entry.timestamp)[-1]
        lines.append(f"  Primary Signals: {latest.primary_signals}")
        lines.append(f"  Secondary Signals: {latest.secondary_signals}")
        lines.append(f"  Ignored Signals: {latest.ignored_signals}")
        lines.append(f"  Risk Salience: {latest.risk_salience}")
        lines.append(f"  Deprioritized Risks: {latest.deprioritized_risks}")
        lines.append(f"  Attention Triggers: {latest.attention_triggers}")
        lines.append(f"  Attention Suppressors: {latest.attention_suppressors}")

    lines.append("\n--- Salience Continuity Failures ---")
    if salience_cont_state and salience_cont_state.failed_surfaces:
        lines.append(str([failure.value for failure in salience_cont_state.failed_surfaces]))
    else:
        lines.append("[]")

    lines.append("\n--- Perceptual Drift Flags ---")
    if perceptual_drift_state and perceptual_drift_state.failed_surfaces:
        lines.append(str([failure.value for failure in perceptual_drift_state.failed_surfaces]))
    else:
        lines.append("[]")

    lines.extend(["", "====================================", ""])
    return "\n".join(lines)


def salience_panel(
    salience_ledger: SalienceLedger,
    salience_cont_state: SalienceContinuityState | None,
    perceptual_drift_state: PerceptualDriftState | None,
    *,
    stream: IO[str] | None = None,
) -> str:
    text = format_salience_panel(salience_ledger, salience_cont_state, perceptual_drift_state)
    out = stream if stream is not None else sys.stdout
    out.write(text)
    if stream is None:
        out.flush()
    return text
