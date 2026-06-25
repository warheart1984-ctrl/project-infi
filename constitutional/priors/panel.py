"""Prior Continuity Panel — epistemic audit of steward priors."""

from __future__ import annotations

import sys
from typing import IO

from constitutional.core.articles import ARTICLE_Q7_REFERENCE
from constitutional.priors.drift_detector import PriorDriftState, StewardPriorMap
from constitutional.priors.ledger import StewardshipPriorLedger


def format_prior_continuity_panel(
    prior_ledger: StewardshipPriorLedger,
    prior_drift_state: PriorDriftState | None,
    steward_priors: StewardPriorMap,
) -> str:
    historical_expected: set[str] = set()
    historical_risks: set[str] = set()
    for entry in prior_ledger.entries:
        historical_expected.update(entry.expected_signals)
        historical_risks.update(entry.expected_risks)

    lines: list[str] = [
        "",
        f"=== PRIOR CONTINUITY PANEL ({ARTICLE_Q7_REFERENCE}) ===",
        "\n--- Historical Priors ---",
        f"Expected Signals: {sorted(historical_expected)}",
        f"Expected Risks: {sorted(historical_risks)}",
        "\n--- Current Steward Priors ---",
        f"Expected Signals: {steward_priors.expected_signals}",
        f"Expected Risks: {steward_priors.expected_risks}",
        f"Assumed Stabilities: {steward_priors.assumed_stabilities}",
        f"Assumed Volatilities: {steward_priors.assumed_volatilities}",
        "\n--- Prior Drift Failures ---",
    ]

    if prior_drift_state and prior_drift_state.failed_surfaces:
        lines.append(str([failure.value for failure in prior_drift_state.failed_surfaces]))
        lines.extend(
            [
                "\n--- Drift Cases ---",
                f"Drift: {prior_drift_state.drift_cases}",
                f"Inversions: {prior_drift_state.inversions}",
                f"Blindspots: {prior_drift_state.blindspots}",
                f"Collapses: {prior_drift_state.collapses}",
                f"Overfits: {prior_drift_state.overfits}",
            ]
        )
    else:
        lines.append("[]")

    lines.extend(["", "====================================", ""])
    return "\n".join(lines)


def prior_continuity_panel(
    prior_ledger: StewardshipPriorLedger,
    prior_drift_state: PriorDriftState | None,
    steward_priors: StewardPriorMap,
    *,
    stream: IO[str] | None = None,
) -> str:
    text = format_prior_continuity_panel(prior_ledger, prior_drift_state, steward_priors)
    out = stream if stream is not None else sys.stdout
    out.write(text)
    if stream is None:
        out.flush()
    return text
