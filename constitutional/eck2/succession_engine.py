"""ECK-2 Succession Engine — dual-pipeline gate replacing ECK-1 gate."""

from __future__ import annotations

from constitutional.eck1.succession_gate import check_eck1_succession_gate
from constitutional.eck2.models import ECK2PipelineResult
from constitutional.eck2.runtime import load_eck2_pipeline
from constitutional.eck2.spec import ECK2_MIN_DRIFT_SYMMETRY_INDEX
from constitutional.jpss.drift import detect_jpss_drift
from constitutional.jpss.invariant_drift import load_invariant_drift_state
from constitutional.jpss.invariant_register import load_invariant_register
from constitutional.jpss.jpss_i_spec import ECK2_MIN_INVARIANT_DRIFT_INDEX
from constitutional.jpss.runtime import load_jpss_cycle
from constitutional.jpss.stewardship_balancing_test import load_stewardship_balancing_result
from constitutional.runtime.runtime import ConstitutionalStateRuntime


def check_eck2_succession_gate(csr: ConstitutionalStateRuntime) -> tuple[bool, str]:
    """A steward may inherit authority only if both pipelines pass."""
    eck1_ready, eck1_message = check_eck1_succession_gate(csr)
    if not eck1_ready:
        return False, f"ECK-2 blocked (ECK-1): {eck1_message}"

    cycle = load_jpss_cycle(csr)
    if cycle is None:
        return False, "ECK-2 blocked: no JPSS formation cycle preserved."

    drift = detect_jpss_drift(csr, decision_id=cycle.decision_id, cycle=cycle)
    if drift.active_drifts:
        classes = ", ".join(finding.drift_class for finding in drift.active_drifts)
        return False, f"ECK-2 blocked: JPSS drift detected ({classes})."

    pipeline = load_eck2_pipeline(csr)
    if pipeline is None:
        return False, "ECK-2 blocked: dual-pipeline result not preserved."

    if not pipeline.reconstruction.reconstructable:
        missing = ", ".join(pipeline.reconstruction.missing_layers)
        return False, f"ECK-2 blocked: reconstruction incomplete ({missing})."

    if pipeline.drift_symmetry.symmetry_index < ECK2_MIN_DRIFT_SYMMETRY_INDEX:
        return False, (
            f"ECK-2 blocked: Drift Symmetry Index {pipeline.drift_symmetry.symmetry_index:.2f} "
            f"< {ECK2_MIN_DRIFT_SYMMETRY_INDEX:.2f}"
        )

    invariant_register = load_invariant_register(csr)
    if not invariant_register.entries:
        return False, "ECK-2 blocked: invariant register not preserved."

    invariant_drift = pipeline.invariant_drift or load_invariant_drift_state(csr)
    if invariant_drift is None:
        return False, "ECK-2 blocked: invariant drift state not evaluated."

    if invariant_drift.drift_index < ECK2_MIN_INVARIANT_DRIFT_INDEX:
        surfaces = ", ".join(f.value for f in invariant_drift.failed_surfaces)
        return False, (
            f"ECK-2 blocked: Invariant Drift Index {invariant_drift.drift_index:.2f} "
            f"< {ECK2_MIN_INVARIANT_DRIFT_INDEX:.2f} ({surfaces})."
        )

    stewardship = pipeline.stewardship_balancing or load_stewardship_balancing_result(csr)
    if stewardship is None or not stewardship.passed:
        return False, "ECK-2 blocked: stewardship balancing test not passed."

    return True, "ECK-2 dual-pipeline succession gate satisfied."


def run_eck2_succession_evaluation(
    csr: ConstitutionalStateRuntime,
) -> tuple[bool, str, ECK2PipelineResult | None]:
    ready, message = check_eck2_succession_gate(csr)
    pipeline = load_eck2_pipeline(csr)
    return ready, message, pipeline
