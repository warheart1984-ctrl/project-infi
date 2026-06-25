"""Failure register succession gates — ECK-1 failure history continuity."""

from __future__ import annotations

from constitutional.eck1.failure_history_runtime import (
    FAILURE_CONTINUITY_MIN_INDEX,
    FailureHistoryRuntime,
    load_failure_history_state,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime


def succession_failure_continuity_ready(
    csr: ConstitutionalStateRuntime,
    *,
    min_index: float | None = None,
) -> tuple[bool, list[str]]:
    threshold = min_index if min_index is not None else FAILURE_CONTINUITY_MIN_INDEX
    state = load_failure_history_state(csr)
    if state is None:
        state = FailureHistoryRuntime(csr).run()
    if state.failure_continuity_index < threshold:
        return False, [
            f"failure_continuity_index_{state.failure_continuity_index:.2f}_below_{threshold:.2f}"
        ]
    if state.failed_surfaces:
        codes = [failure.value for failure in state.failed_surfaces]
        return False, [f"failure_history_failures_{','.join(codes)}"]
    return True, []
