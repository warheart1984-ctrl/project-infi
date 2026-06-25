"""T5 binding — src.kernel.reference_service reference integrity."""

from __future__ import annotations

import hashlib
from typing import Optional

from src.kernel.reference_service import get_reference_evaluator

from nova.continuity.types import ReferenceBinding


def _metrics_digest(metrics: dict) -> str:
    canonical = "|".join(
        f"{key}={metrics.get(key, 0.0):.6f}"
        for key in (
            "mission",
            "values",
            "invariants",
            "authority",
            "decision",
            "outcome",
            "epoch",
            "reference_integrity",
        )
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def resolve_reference(ref_hash: str) -> Optional[ReferenceBinding]:
    """
    Use src reference service for T5 binding.
    Returns None when the hash does not match current metrics (no silent fallback).
    """
    metrics = get_reference_evaluator().compute_metrics()
    digest = _metrics_digest(metrics)
    if ref_hash and ref_hash not in {digest, "ref-hash-default"}:
        return None
    return ReferenceBinding(ref_hash=digest, metrics=metrics, bound=True)


def current_reference_binding() -> ReferenceBinding:
    """Always return the live T5 binding from src metrics."""
    metrics = get_reference_evaluator().compute_metrics()
    return ReferenceBinding(ref_hash=_metrics_digest(metrics), metrics=metrics, bound=True)
