"""IMXP governance wrapper — consult MGM-2 policies without forking platform/exchange/."""

from __future__ import annotations

from typing import Any


def check_imxp_outbound_permeability(envelope: dict[str, Any]) -> dict[str, Any]:
    try:
        from src.multi_organism_governance_membrane_runtime import multi_organism_governance_membrane_runtime

        return multi_organism_governance_membrane_runtime.check_exchange_permeability(envelope)
    except Exception as exc:
        return {"allowed": True, "reason": "wrapper_unavailable", "error": str(exc)[:120]}


def check_imxp_inbound_permeability(envelope: dict[str, Any]) -> dict[str, Any]:
    result = check_imxp_outbound_permeability(envelope)
    if not result.get("allowed"):
        return result
    if not envelope.get("signature"):
        return {"allowed": False, "reason": "unsigned_envelope"}
    return result
