"""Stewardship Legitimacy Gate — who may alter the invariant layer."""

from __future__ import annotations

from constitutional.legitimacy.legitimacy_criterion import load_legitimacy_criterion_result
from constitutional.legitimacy.legitimacy_process import load_legitimacy_process_result, load_legitimacy_ratification
from constitutional.legitimacy.legitimacy_receipts import load_legitimacy_receipts
from constitutional.legitimacy.legitimacy_drift import detect_legitimacy_drift, load_legitimacy_drift_state
from constitutional.legitimacy.legitimacy_exam import load_legitimacy_exam_result, run_legitimacy_exam
from constitutional.legitimacy.legitimacy_register import load_legitimacy_register
from constitutional.legitimacy.spec import MIN_LEGITIMACY_INDEX
from constitutional.runtime.runtime import ConstitutionalStateRuntime


def check_steward_certification(
    csr: ConstitutionalStateRuntime,
    steward_id: str,
) -> tuple[bool, str]:
    """Verify steward is actively certified with passing exam and reconstruction criterion."""
    register = load_legitimacy_register(csr)
    entry = register.get_active(steward_id)
    if entry is None:
        return False, f"Legitimacy blocked: {steward_id} is not a certified steward."

    if entry.legitimacy_index < MIN_LEGITIMACY_INDEX:
        return False, (
            f"Legitimacy blocked: {steward_id} legitimacy index "
            f"{entry.legitimacy_index:.2f} < {MIN_LEGITIMACY_INDEX:.2f}."
        )

    criterion = load_legitimacy_criterion_result(csr, steward_id)
    if criterion is None or not criterion.passed:
        return False, f"Legitimacy blocked: {steward_id} has not demonstrated reconstruction criterion."

    process = load_legitimacy_process_result(csr, steward_id)
    if process is None or not process.passed:
        return False, f"Legitimacy blocked: {steward_id} has not completed Protocol v1.0 process."

    ratification = load_legitimacy_ratification(csr, steward_id)
    if ratification is None or not ratification.plural or ratification.capture_detected:
        return False, f"Legitimacy blocked: {steward_id} lacks plural, capture-free ratification."

    receipts = load_legitimacy_receipts(csr, steward_id)
    if receipts is None or not receipts.complete:
        return False, f"Legitimacy blocked: {steward_id} legitimacy receipts incomplete."

    exam = load_legitimacy_exam_result(csr)
    if exam is None or not exam.passed:
        return False, f"Legitimacy blocked: stewardship legitimacy exam not passed for {steward_id}."

    return True, f"{steward_id} is a certified steward with demonstrated reconstruction competence."


def may_alter_invariant_layer(
    csr: ConstitutionalStateRuntime,
    steward_id: str,
) -> tuple[bool, str]:
    """Authority by reconstruction: only certified stewards under plurality may touch invariants."""
    certified, cert_message = check_steward_certification(csr, steward_id)
    if not certified:
        return False, cert_message

    register = load_legitimacy_register(csr)
    if not register.plurality_satisfied():
        return False, (
            f"Legitimacy blocked: plurality not satisfied "
            f"({len(register.active_stewards())} < {register.minimum_plurality} certified stewards)."
        )

    drift = load_legitimacy_drift_state(csr) or detect_legitimacy_drift(csr)
    if drift.drift_index < MIN_LEGITIMACY_INDEX:
        surfaces = ", ".join(f.value for f in drift.failed_surfaces)
        return False, f"Legitimacy blocked: legitimacy drift detected ({surfaces})."

    return True, (
        f"{steward_id} is legitimately authorized to propose invariant-layer changes "
        f"(authority by reconstruction, plurality satisfied)."
    )


def check_stewardship_legitimacy_gate(
    csr: ConstitutionalStateRuntime,
    steward_id: str,
) -> tuple[bool, str]:
    """Full legitimacy gate for succession and invariant governance."""
    exam = run_legitimacy_exam(csr, steward_id)
    if not exam.passed:
        blockers = "; ".join(exam.blockers) if exam.blockers else "exam not passed"
        return False, f"Stewardship legitimacy gate blocked: {blockers}"

    return may_alter_invariant_layer(csr, steward_id)
