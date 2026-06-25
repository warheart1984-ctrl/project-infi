"""CRK-T1 boundary — invariants are fitness, not kernel objects."""

from __future__ import annotations

from src.continuity.crk1_compliance import scan_forbidden_invariant_objects


def test_no_cit_mit_eit_attention_kernel_objects() -> None:
    violations = scan_forbidden_invariant_objects()
    assert not violations, f"invariant object names found: {violations}"
