"""Provider organ registry — O_i = (I, E, F, K) for URG routing."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ugr.mission.tenant_manifold import tenant_path_slug
from src.ugr.platform.tenant_registry import TenantRegistry, normalize_tenant_id


ORGAN_STATUS_ADMITTED = "admitted"
ORGAN_STATUS_SUSPENDED = "suspended"
ORGAN_STATUS_EVICTED = "evicted"


def _default_organs_path() -> Path:
    env_path = os.getenv("URG_PROVIDER_ORGANS_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    return Path(__file__).resolve().parents[3] / "deploy" / "ugr" / "provider-organs.json"


def _tenant_organs_path(tenant_id: str) -> Path:
    slug = tenant_path_slug(normalize_tenant_id(tenant_id))
    return Path(__file__).resolve().parents[3] / "deploy" / "ugr" / "tenants" / slug / "provider-organs.json"


@dataclass(frozen=True)
class ProviderOrgan:
    """One governed provider organ."""

    organ_id: str
    identity: dict[str, Any]
    envelope: dict[str, Any]
    function: dict[str, Any]
    contract: dict[str, Any]
    tenant_scope: str = "global"
    status: str = ORGAN_STATUS_ADMITTED
    governance_tier: str = "standard"
    trust_score: float = 0.5
    admission_receipt_id: str | None = None

    @property
    def provider(self) -> str:
        return str(self.contract.get("provider") or "local")

    @property
    def tier(self) -> str:
        return str(self.identity.get("tier") or "mid")

    @property
    def max_cost_units(self) -> float:
        return float(self.contract.get("max_cost_units") or 0)

    @property
    def cost_contract(self) -> dict[str, Any]:
        return dict(self.contract.get("cost_contract") or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "organ_id": self.organ_id,
            "identity": dict(self.identity),
            "envelope": dict(self.envelope),
            "function": dict(self.function),
            "contract": dict(self.contract),
            "tenant_scope": self.tenant_scope,
            "status": self.status,
            "governance_tier": self.governance_tier,
            "trust_score": self.trust_score,
            "admission_receipt_id": self.admission_receipt_id,
        }


class ProviderOrganRegistry:
    """Load global base + tenant overlay; filter by tenant visibility and status."""

    def __init__(
        self,
        config_path: str | Path | None = None,
        *,
        tenant_id: str | None = None,
        tenant_registry: TenantRegistry | None = None,
    ):
        self.tenant_id = normalize_tenant_id(tenant_id or "global")
        self.base_path = Path(config_path) if config_path else _default_organs_path()
        self.tenant_registry = tenant_registry or TenantRegistry()
        self._organs: dict[str, ProviderOrgan] = {}
        self._load()

    def _parse_organ(self, organ_id: str, spec: dict[str, Any]) -> ProviderOrgan:
        contract = dict(spec.get("contract") or {})
        if "cost_contract" not in contract and contract.get("max_cost_units"):
            contract.setdefault(
                "cost_contract",
                {
                    "cost_per_call": float(contract.get("max_cost_units") or 0),
                    "cost_per_token": None,
                    "region_multiplier": {},
                },
            )
        return ProviderOrgan(
            organ_id=str(organ_id),
            identity=dict(spec.get("identity") or {}),
            envelope=dict(spec.get("envelope") or {}),
            function=dict(spec.get("function") or {}),
            contract=contract,
            tenant_scope=str(spec.get("tenant_scope") or "global"),
            status=str(spec.get("status") or ORGAN_STATUS_ADMITTED),
            governance_tier=str(spec.get("governance_tier") or "standard"),
            trust_score=float(spec.get("trust_score", 0.5)),
            admission_receipt_id=spec.get("admission_receipt_id"),
        )

    def _load_payload(self, path: Path) -> None:
        if not path.exists():
            return
        payload = json.loads(path.read_text(encoding="utf-8"))
        for organ_id, spec in dict(payload.get("organs") or {}).items():
            self._organs[str(organ_id)] = self._parse_organ(str(organ_id), dict(spec))

    def _load(self) -> None:
        self._load_payload(self.base_path)
        overlay = _tenant_organs_path(self.tenant_id)
        if overlay.exists():
            self._load_payload(overlay)
        self._apply_tenant_filter()

    def _apply_tenant_filter(self) -> None:
        spec = self.tenant_registry.get(self.tenant_id)
        allowed_providers: set[str] | None = None
        if spec and spec.allowed_providers:
            allowed_providers = set(spec.allowed_providers)
        filtered: dict[str, ProviderOrgan] = {}
        for organ_id, organ in self._organs.items():
            if organ.status == ORGAN_STATUS_EVICTED:
                continue
            scope = normalize_tenant_id(organ.tenant_scope)
            if scope not in {self.tenant_id, "global"}:
                continue
            if allowed_providers is not None and organ.provider not in allowed_providers:
                continue
            filtered[organ_id] = organ
        self._organs = filtered

    def get(self, organ_id: str) -> ProviderOrgan | None:
        organ = self._organs.get(str(organ_id or "").strip())
        if organ and organ.status == ORGAN_STATUS_SUSPENDED:
            return organ
        return organ

    def list_organs(self, *, include_suspended: bool = False) -> list[ProviderOrgan]:
        organs = list(self._organs.values())
        if include_suspended:
            return organs
        return [o for o in organs if o.status == ORGAN_STATUS_ADMITTED]

    def admitted_organ_ids(self) -> list[str]:
        return sorted(
            oid for oid, o in self._organs.items() if o.status == ORGAN_STATUS_ADMITTED
        )

    def routable_organs(self) -> list[ProviderOrgan]:
        """Organs eligible for auto-assign (admitted only)."""
        return [o for o in self._organs.values() if o.status == ORGAN_STATUS_ADMITTED]

    def build_proposal(
        self,
        organ: ProviderOrgan,
        *,
        mission_id: str,
        action_id: str,
        step: dict[str, Any],
        intent: str,
    ) -> dict[str, Any]:
        """Bounded proposal envelope for a mission step (no direct provider I/O)."""
        objective = str(step.get("objective") or "").strip()
        return {
            "module_id": "urg.provider_organ",
            "version": "1.0",
            "status": "PROPOSED",
            "reason": "mission_step_provider_proposal",
            "proposal_only": bool(organ.envelope.get("proposal_only", True)),
            "execution_authority": "none",
            "mutation_authority": "none",
            "mission_id": mission_id,
            "action_id": action_id,
            "organ_id": organ.organ_id,
            "provider_request": {
                "provider": organ.provider,
                "provider_label": str(organ.identity.get("label") or organ.organ_id),
                "route_id": f"urg.mission.{organ.tier}",
                "response_mode": str(organ.envelope.get("response_mode") or "think"),
                "execution_backend": str(organ.envelope.get("execution_backend") or "local"),
                "instruction": objective[:500],
                "generation_overrides": {"temperature": 0, "temperature_max": 0},
            },
            "intent": intent,
            "tier": organ.tier,
        }

    def upsert_organ(self, organ_id: str, spec: dict[str, Any]) -> ProviderOrgan:
        """In-memory upsert (used by governance apply)."""
        organ = self._parse_organ(organ_id, spec)
        self._organs[organ_id] = organ
        return organ

    def save_tenant_overlay(self) -> Path:
        """Persist tenant-scoped organs to overlay file."""
        path = _tenant_organs_path(self.tenant_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        tenant_organs = {
            oid: o.to_dict()
            for oid, o in self._organs.items()
            if normalize_tenant_id(o.tenant_scope) == self.tenant_id
        }
        payload = {"registry_version": "1.0", "organs": tenant_organs}
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path
