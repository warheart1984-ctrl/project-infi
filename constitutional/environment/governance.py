"""Decision environment succession gates — Article Q-5."""

from __future__ import annotations

from constitutional.core.articles import SUCCESSION_MIN_DECISION_ENVIRONMENT
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.significance.decision_environment_runtime import (
    DecisionEnvironmentRuntime,
    load_decision_environment_state,
)


def succession_decision_environment_ready(
    csr: ConstitutionalStateRuntime,
    *,
    min_index: float | None = None,
) -> tuple[bool, list[str]]:
    threshold = min_index if min_index is not None else SUCCESSION_MIN_DECISION_ENVIRONMENT
    try:
        state = load_decision_environment_state(csr)
    except KeyError:
        state = DecisionEnvironmentRuntime(csr).run()
    if state.environment_health_index < threshold:
        return False, [
            f"decision_environment_index_{state.environment_health_index:.2f}_below_{threshold:.2f}"
        ]
    if state.failed_surfaces:
        codes = [failure.value for failure in state.failed_surfaces]
        return False, [f"decision_environment_failures_{','.join(codes)}"]
    return True, []
