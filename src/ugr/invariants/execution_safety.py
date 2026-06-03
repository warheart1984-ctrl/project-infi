"""Execution Safety Invariant — cloud-level gate before execution_committed."""

from __future__ import annotations

from typing import Any

from src.ugr.invariants.cloud_invariants import check_cloud_boundary, has_hard_fail
from src.ugr.invariants.cloud_manifold import CloudManifoldState


def _invariant(name: str, status: str, details: str = "") -> dict[str, Any]:
    return {"family": name, "status": status, "details": details}


def check_execution_safety(
    mission_state: dict[str, Any],
    step_assignment: dict[str, Any],
    *,
    manifold: CloudManifoldState | None = None,
    ledger_write_ok: bool = True,
    pending_receipt: bool = True,
) -> list[dict[str, Any]]:
    """
    No execution_committed unless:
    - Step lies in B_cloud(M)
    - Ledger write succeeded
    - Mission has pending receipt path (manifold stamped)
    """
    results: list[dict[str, Any]] = []
    frozen = manifold
    if frozen is None:
        frozen = CloudManifoldState.from_dict(mission_state.get("cloud_manifold") or {})

    if not frozen.cloud_identity_hash or not frozen.boundary_digest:
        results.append(
            _invariant("cloud_execution_safety", "hard_fail", "missing cloud manifold on mission")
        )
        return results

    boundary_results = check_cloud_boundary(mission_state, step_assignment, manifold=frozen)
    results.extend(boundary_results)

    if not ledger_write_ok:
        results.append(_invariant("cloud_execution_safety", "hard_fail", "ledger write required before commit"))

    if not pending_receipt:
        results.append(
            _invariant("cloud_execution_safety", "hard_fail", "valid MissionReceipt path required before commit")
        )

    if not has_hard_fail(results):
        results.append(_invariant("cloud_execution_safety", "pass", "execution boundary and ledger law satisfied"))

    return results
