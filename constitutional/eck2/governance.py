"""ECK-2 governance helpers for succession integration."""

from __future__ import annotations

from constitutional.eck2.succession_engine import check_eck2_succession_gate
from constitutional.eck2.runtime import load_eck2_pipeline
from constitutional.runtime.runtime import ConstitutionalStateRuntime


def succession_eck2_dual_pipeline_ready(
    csr: ConstitutionalStateRuntime,
) -> tuple[bool, list[str]]:
    """When an ECK-2 pipeline exists, require the dual-pipeline gate."""
    pipeline = load_eck2_pipeline(csr)
    if pipeline is None:
        return True, []
    ready, message = check_eck2_succession_gate(csr)
    if ready:
        return True, []
    return False, [message]
