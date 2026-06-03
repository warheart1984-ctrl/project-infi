"""URG ingress law — if it did not pass through URG, it does not exist."""

from __future__ import annotations

from hashlib import sha256
import json
import time
from typing import Any
from uuid import uuid4

from src.ugr.platform.tenant_registry import normalize_tenant_id


URG_INGRESS_VERSION = "1.2"
URG_INGRESS_SURFACE = "urg.mission.ingress"


class UrgIngressLaw:
    """Stamp and validate mission ingress before any cloud routing."""

    def stamp_mission(self, request: dict[str, Any]) -> dict[str, Any]:
        """Open a mission under URG ingress (required for ledger existence)."""
        payload = dict(request or {})
        mission_seed = _stable_json(
            {
                "operator_id": payload.get("operator_id"),
                "tenant_id": payload.get("tenant_id"),
                "aais_instance_id": payload.get("aais_instance_id"),
                "intent": payload.get("intent"),
                "objective": payload.get("objective"),
            }
        )
        digest = sha256(mission_seed.encode("utf-8")).hexdigest()[:12]
        provided = str(payload.get("mission_id") or "").strip()
        if provided:
            mission_id = provided
            mission_slug = None
        else:
            mission_id = str(uuid4())
            mission_slug = f"mission-{digest}-{mission_id.split('-')[0]}"
        return {
            "ingress_version": URG_INGRESS_VERSION,
            "ingress_surface": URG_INGRESS_SURFACE,
            "mission_id": mission_id,
            "mission_slug": mission_slug,
            "stamped_at": int(time.time()),
            "stamp_hash": sha256(f"{mission_id}:{URG_INGRESS_SURFACE}".encode()).hexdigest()[:16],
            "law": "if_not_through_urg_it_does_not_exist",
            "operator_id": str(payload.get("operator_id") or "").strip(),
            "tenant_id": normalize_tenant_id(payload.get("tenant_id") or "global"),
            "aais_instance_id": str(payload.get("aais_instance_id") or "").strip(),
            "status": "stamped",
        }

    def validate_stamp(self, ingress: dict[str, Any] | None) -> tuple[bool, str]:
        if not ingress:
            return False, "missing_urg_ingress_stamp"
        if ingress.get("ingress_surface") != URG_INGRESS_SURFACE:
            return False, "invalid_ingress_surface"
        if not str(ingress.get("mission_id") or "").strip():
            return False, "missing_mission_id"
        if ingress.get("status") != "stamped":
            return False, "ingress_not_stamped"
        return True, "ok"

    def reject_bypass(self, *, reason: str = "direct_provider_bypass") -> dict[str, Any]:
        return {
            "status": "rejected",
            "summary": "URG ingress law: bypass denied",
            "reason": reason,
            "law": "if_not_through_urg_it_does_not_exist",
        }


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
