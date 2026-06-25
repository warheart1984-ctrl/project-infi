"""JPSS-1 drift detection — eight canonical drift classes."""

from __future__ import annotations

from datetime import UTC, datetime

from constitutional.eck1.registers import load_calibration_register, load_environment_register, load_failure_register
from constitutional.jpss.models import JPSSCycleResult, JPSSDriftFinding, JPSSDriftReport
from constitutional.jpss.registers import (
    load_decision_register,
    load_outcome_register,
    load_perception_register,
    load_reflection_register,
)
from constitutional.jpss.spec import JPSS_DRIFT_CLASSES
from constitutional.priors.ledger import load_prior_ledger
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.salience.ledger import load_salience_ledger


def detect_jpss_drift(
    csr: ConstitutionalStateRuntime,
    *,
    decision_id: str | None = None,
    cycle: JPSSCycleResult | None = None,
) -> JPSSDriftReport:
    """Detect drift across all eight JPSS layers for a decision or latest cycle."""
    now = datetime.now(UTC).replace(microsecond=0)
    target_id = decision_id or (cycle.decision_id if cycle else None)

    env_register = load_environment_register(csr)
    perception_register = load_perception_register(csr)
    salience_ledger = load_salience_ledger(csr)
    calibration_register = load_calibration_register(csr)
    decision_register = load_decision_register(csr)
    outcome_register = load_outcome_register(csr)
    reflection_register = load_reflection_register(csr)
    failure_register = load_failure_register(csr)
    prior_ledger = load_prior_ledger(csr)

    findings: list[JPSSDriftFinding] = []

    env_entry = None
    if target_id:
        env_entry = next(
            (entry for entry in reversed(env_register.entries) if entry.decision_id == target_id),
            None,
        )
    findings.append(
        JPSSDriftFinding(
            drift_class="environmental_drift",
            detected=target_id is not None and env_entry is None,
            description="Environment register missing decision anchor." if env_entry is None and target_id else "",
        )
    )

    perception_entry = perception_register.latest_for_decision(target_id) if target_id else None
    findings.append(
        JPSSDriftFinding(
            drift_class="perceptual_drift",
            detected=target_id is not None and perception_entry is None,
            description="Perception register missing decision anchor." if perception_entry is None and target_id else "",
        )
    )

    salience_entries = [entry for entry in salience_ledger.entries if entry.decision_id == target_id] if target_id else []
    findings.append(
        JPSSDriftFinding(
            drift_class="salience_drift",
            detected=target_id is not None and not salience_entries,
            description="Salience ledger missing decision anchor." if not salience_entries and target_id else "",
        )
    )

    calibration_entry = calibration_register.latest_for_decision(target_id) if target_id else None
    findings.append(
        JPSSDriftFinding(
            drift_class="calibration_drift",
            detected=target_id is not None and calibration_entry is None,
            description="Calibration register missing decision anchor." if calibration_entry is None and target_id else "",
        )
    )

    decision_entry = decision_register.latest_for_decision(target_id) if target_id else None
    findings.append(
        JPSSDriftFinding(
            drift_class="decision_drift",
            detected=target_id is not None and decision_entry is None,
            description="Decision register missing decision anchor." if decision_entry is None and target_id else "",
        )
    )

    outcome_entry = outcome_register.latest_for_decision(target_id) if target_id else None
    findings.append(
        JPSSDriftFinding(
            drift_class="outcome_drift",
            detected=target_id is not None and outcome_entry is None,
            description="Outcome register missing decision anchor." if outcome_entry is None and target_id else "",
        )
    )

    reflection_entry = reflection_register.latest_for_decision(target_id) if target_id else None
    findings.append(
        JPSSDriftFinding(
            drift_class="reflection_drift",
            detected=target_id is not None and reflection_entry is None,
            description="Reflection register missing decision anchor." if reflection_entry is None and target_id else "",
        )
    )

    prior_entries = [entry for entry in prior_ledger.entries if entry.decision_id == target_id] if target_id else []
    unresolved_failures = failure_register.unresolved()
    findings.append(
        JPSSDriftFinding(
            drift_class="failure_drift",
            detected=bool(unresolved_failures),
            description=f"{len(unresolved_failures)} unresolved failure entries." if unresolved_failures else "",
            correctable=True,
        )
    )

    if cycle and target_id:
        if cycle.perception.available_signals and not prior_entries:
            for finding in findings:
                if finding.drift_class == "perceptual_drift":
                    finding.detected = True
                    finding.description = "Cycle perception not mirrored in prior ledger."

    drift_detectable = len(findings) == len(JPSS_DRIFT_CLASSES)
    drift_correctable = all(finding.correctable for finding in findings if finding.detected)

    return JPSSDriftReport(
        decision_id=target_id,
        findings=findings,
        drift_detectable=drift_detectable,
        drift_correctable=drift_correctable,
        captured_at=now,
    )


def detect_jpss_drift_with_taxonomy(
    csr: ConstitutionalStateRuntime,
    *,
    decision_id: str | None = None,
    cycle: JPSSCycleResult | None = None,
):
    """Layer drift detection plus full JPSS drift taxonomy sub-types."""
    from constitutional.jpss.drift_taxonomy import build_drift_taxonomy_report

    layer_report = detect_jpss_drift(csr, decision_id=decision_id, cycle=cycle)
    return build_drift_taxonomy_report(layer_report)
