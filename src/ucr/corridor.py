"""Corridor and Lane governance model for UCR."""

# Mythic: Governance Corridor
# Engineering: CorridorGovernanceModel
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from src.ucr.authority_envelope import AuthorityEnvelope, RISK_ORDER
from src.ucr.binary_law_key import CANONICAL_U128

RISK_LEVELS = tuple(RISK_ORDER.keys())


@dataclass(slots=True)
class AuditPolicy:
    require_full_ledger: bool
    retention_days: int
    require_human_review: bool


@dataclass(slots=True)
class ResourceBounds:
    max_tokens: int
    max_latency_ms: int
    max_fanout: int

    @property
    def max_latency(self) -> int:
        return self.max_latency_ms


@dataclass(slots=True)
class LaneProfile:
    lane_id: UUID
    name: str
    role: str
    allowed_risk: str
    allowed_scopes: list[str]
    law_key: int
    resource_bounds: ResourceBounds

    def __post_init__(self) -> None:
        if self.allowed_risk not in RISK_ORDER:
            raise ValueError(f"allowed_risk must be one of {RISK_LEVELS}")
        if self.role not in {"primary", "veto", "advisory", "execution"}:
            raise ValueError("role must be primary|veto|advisory|execution")


@dataclass(slots=True)
class Corridor:
    corridor_id: UUID
    name: str
    owner_id: UUID
    max_risk: str
    default_law: int
    lane_profiles: list[LaneProfile]
    audit_policy: AuditPolicy
    version: int = 1
    created_at: datetime | None = None
    supersedes: UUID | None = None

    def __post_init__(self) -> None:
        if self.max_risk not in RISK_ORDER:
            raise ValueError(f"max_risk must be one of {RISK_LEVELS}")
        if self.version < 1:
            raise ValueError("version must be >= 1")

    def compatible_law_keys(self) -> set[int]:
        keys = {self.default_law}
        keys.update(lane.law_key for lane in self.lane_profiles)
        return keys

    def law_key_compatible(self, law_key: int) -> bool:
        return law_key in self.compatible_law_keys()


def risk_allows(ceiling: str, level: str) -> bool:
    return RISK_ORDER.get(level, 99) <= RISK_ORDER[ceiling]


def scopes_cover(required: list[str], allowed: list[str]) -> bool:
    allowed_set = set(allowed)
    return all(scope in allowed_set for scope in required)


def validate_envelope_against_corridor(
    envelope: AuthorityEnvelope,
    corridor: Corridor,
) -> tuple[bool, str]:
    if not corridor.law_key_compatible(envelope.law_key):
        return False, "envelope law_key not compatible with corridor default or lane law keys"
    if not risk_allows(corridor.max_risk, envelope.permissions.max_risk):
        return False, "envelope permissions.max_risk exceeds corridor.max_risk"
    return True, ""


@dataclass(slots=True)
class CognitiveActAdmission:
    """Minimal act view for lane selection and commit gates."""

    act_id: str
    risk_level: str
    required_scopes: list[str] = field(default_factory=list)
    uses_tools: bool = False
    memory_write: bool = False
    producer_id: str = "ucr.default"
    vetoed: bool = False
    ledger_ref: bytes = b""

    def __post_init__(self) -> None:
        if self.risk_level not in RISK_ORDER:
            raise ValueError(f"risk_level must be one of {RISK_LEVELS}")


def law_key_to_hex(law_key: int) -> str:
    return f"0x{law_key:032X}"


def lane_law_compatible(lane: LaneProfile, envelope: AuthorityEnvelope, corridor: Corridor) -> bool:
    return envelope.law_key in {lane.law_key, corridor.default_law}


def select_eligible_lanes(
    corridor: Corridor,
    act: CognitiveActAdmission,
    envelope: AuthorityEnvelope,
) -> list[LaneProfile]:
    eligible: list[LaneProfile] = []
    for lane in corridor.lane_profiles:
        if not risk_allows(lane.allowed_risk, act.risk_level):
            continue
        if not scopes_cover(act.required_scopes, lane.allowed_scopes):
            continue
        if not lane_law_compatible(lane, envelope, corridor):
            continue
        eligible.append(lane)
    return eligible


# Stable fixture IDs for tests and registry seeds.
NOVA_DEV_CORRIDOR_ID = UUID("11111111-1111-4111-8111-111111111101")
NOVA_DEV_OWNER_ID = UUID("11111111-1111-4111-8111-111111111001")
NOVA_DEV_PRIMARY_LANE_ID = UUID("11111111-1111-4111-8111-111111111201")
NOVA_DEV_VETO_LANE_ID = UUID("11111111-1111-4111-8111-111111111202")

PROD_OPS_CORRIDOR_ID = UUID("22222222-2222-4222-8222-222222222201")
PROD_OPS_OWNER_ID = UUID("22222222-2222-4222-8222-222222222001")
PROD_OPS_PRIMARY_LANE_ID = UUID("22222222-2222-4222-8222-222222222201")
PROD_OPS_EXEC_LANE_ID = UUID("22222222-2222-4222-8222-222222222202")

# Alternate law key for Prod-Ops lane variant (differs only in reserved field for tests).
PROD_OPS_LANE_LAW_KEY = CANONICAL_U128


def build_nova_dev_corridor() -> Corridor:
    return Corridor(
        corridor_id=NOVA_DEV_CORRIDOR_ID,
        name="Nova-Dev",
        owner_id=NOVA_DEV_OWNER_ID,
        max_risk="high",
        default_law=CANONICAL_U128,
        lane_profiles=[
            LaneProfile(
                lane_id=NOVA_DEV_PRIMARY_LANE_ID,
                name="deliberation-primary",
                role="primary",
                allowed_risk="high",
                allowed_scopes=["code_write", "data_read", "tool_call"],
                law_key=CANONICAL_U128,
                resource_bounds=ResourceBounds(max_tokens=8192, max_latency_ms=5000, max_fanout=8),
            ),
            LaneProfile(
                lane_id=NOVA_DEV_VETO_LANE_ID,
                name="safety-veto",
                role="veto",
                allowed_risk="critical",
                allowed_scopes=["data_read"],
                law_key=CANONICAL_U128,
                resource_bounds=ResourceBounds(max_tokens=2048, max_latency_ms=1000, max_fanout=2),
            ),
        ],
        audit_policy=AuditPolicy(
            require_full_ledger=True,
            retention_days=30,
            require_human_review=False,
        ),
        version=1,
    )


def build_prod_ops_corridor() -> Corridor:
    return Corridor(
        corridor_id=PROD_OPS_CORRIDOR_ID,
        name="Prod-Ops",
        owner_id=PROD_OPS_OWNER_ID,
        max_risk="critical",
        default_law=CANONICAL_U128,
        lane_profiles=[
            LaneProfile(
                lane_id=PROD_OPS_PRIMARY_LANE_ID,
                name="ops-primary",
                role="primary",
                allowed_risk="high",
                allowed_scopes=["data_read", "tool_call"],
                law_key=CANONICAL_U128,
                resource_bounds=ResourceBounds(max_tokens=4096, max_latency_ms=3000, max_fanout=4),
            ),
            LaneProfile(
                lane_id=PROD_OPS_EXEC_LANE_ID,
                name="ops-execution",
                role="execution",
                allowed_risk="critical",
                allowed_scopes=["tool_call"],
                law_key=PROD_OPS_LANE_LAW_KEY,
                resource_bounds=ResourceBounds(max_tokens=2048, max_latency_ms=2000, max_fanout=2),
            ),
        ],
        audit_policy=AuditPolicy(
            require_full_ledger=True,
            retention_days=365,
            require_human_review=True,
        ),
        version=1,
    )
