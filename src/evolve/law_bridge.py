"""Bridge EvolveEngine requests into the live AAIS evolve law contract."""

from __future__ import annotations

from typing import Any

from evolve_engine.universal_language import enforce_foundation_laws


def enforce_laws(
    artifact: Any,
    action: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Apply the canonical Evolve foundation-law contract.

    The live EvolveEngine service depends on a narrow AAIS bridge module at
    `src.evolve.law_bridge`. This adapter keeps that import stable while
    delegating the actual enforcement to the canonical EvolveEngine universal
    language contract.
    """

    return enforce_foundation_laws(artifact=artifact, action=action, context=dict(context or {}))
