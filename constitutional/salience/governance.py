"""Salience succession gates — continuity and judgment readiness."""

from __future__ import annotations

from constitutional.core.articles import SUCCESSION_MIN_SALIENCE_INDEX
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.salience.continuity_runtime import (
    SALIENCE_CONTINUITY_MIN_INDEX,
    SalienceContinuityRuntime,
    load_salience_continuity_state,
)
from constitutional.salience.judgment_runtime import (
    SalienceJudgmentTest,
    StewardSalienceAnswer,
    load_salience_judgment_state,
)
from constitutional.salience.perceptual_drift import (
    PerceptualDriftDetector,
    load_perceptual_drift_state,
)


def succession_salience_judgment_ready(
    csr: ConstitutionalStateRuntime | None = None,
    *,
    steward_answers: dict[str, StewardSalienceAnswer] | None = None,
) -> tuple[bool, list[str]]:
    if csr is None and steward_answers is None:
        return False, ["salience_judgment_not_evaluated"]

    if steward_answers is not None:
        result = SalienceJudgmentTest().evaluate(steward_answers)
        if not result.passed:
            return False, [f"salience_judgment_failed_score_{result.score:.2f}", *result.false_signals]
        return True, []

    state = load_salience_judgment_state(csr)  # type: ignore[arg-type]
    if state is None or state.last_result is None:
        return False, ["salience_judgment_not_completed"]
    if not state.passed:
        return False, [f"salience_judgment_failed_score_{state.last_result.score:.2f}"]
    return True, []


def succession_salience_continuity_ready(
    csr: ConstitutionalStateRuntime,
    *,
    min_index: float | None = None,
) -> tuple[bool, list[str]]:
    threshold = min_index if min_index is not None else SUCCESSION_MIN_SALIENCE_INDEX
    state = load_salience_continuity_state(csr)
    if state is None:
        state = SalienceContinuityRuntime(csr).run()
    if state.salience_index < threshold:
        return False, [f"salience_continuity_index_{state.salience_index:.2f}_below_{threshold:.2f}"]
    if state.failed_surfaces:
        codes = [failure.value for failure in state.failed_surfaces]
        return False, [f"salience_continuity_failures_{','.join(codes)}"]
    return True, []


def succession_perceptual_drift_ready(
    csr: ConstitutionalStateRuntime,
    *,
    min_index: float = 0.8,
) -> tuple[bool, list[str]]:
    from constitutional.salience.ledger import load_salience_ledger
    from constitutional.salience.perceptual_drift import PerceptualDriftDetector, StewardSalienceMap

    ledger = load_salience_ledger(csr)
    primary: list[str] = []
    secondary: list[str] = []
    ignored: list[str] = []
    for entry in ledger.entries:
        primary.extend(entry.primary_signals)
        secondary.extend(entry.secondary_signals)
        ignored.extend(entry.ignored_signals)
    steward_map = StewardSalienceMap(
        primary_signals=list(dict.fromkeys(primary)),
        secondary_signals=list(dict.fromkeys(secondary)),
        ignored_signals=list(dict.fromkeys(ignored)),
    )
    state = load_perceptual_drift_state(csr)
    if state is None:
        state = PerceptualDriftDetector(csr, salience_ledger=ledger, steward_salience_map=steward_map).run()
    if state.drift_index < min_index:
        return False, [f"perceptual_drift_index_{state.drift_index:.2f}_below_{min_index:.2f}"]
    if state.failed_surfaces:
        codes = [failure.value for failure in state.failed_surfaces]
        return False, [f"perceptual_drift_failures_{','.join(codes)}"]
    return True, []


def salience_aware_succession_gate(
    csr: ConstitutionalStateRuntime,
) -> tuple[bool, str]:
    """Salience judgment + continuity gate for succession."""
    judgment_ok, judgment_reasons = succession_salience_judgment_ready(csr)
    if not judgment_ok:
        return False, f"Succession blocked: Salience Judgment failure ({'; '.join(judgment_reasons)})"

    continuity_ok, continuity_reasons = succession_salience_continuity_ready(csr)
    if not continuity_ok:
        return False, f"Succession blocked: Salience Continuity failure ({'; '.join(continuity_reasons)})"

    drift_ok, drift_reasons = succession_perceptual_drift_ready(csr)
    if not drift_ok:
        return False, f"Succession blocked: Perceptual Drift failure ({'; '.join(drift_reasons)})"

    return True, "Salience succession gates satisfied."
