"""Cloud Forge rail scheduler types (aais.cloud_forge.rail.v1)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

CONTRACT_VERSION = "aais.cloud_forge.rail.v1"
CLAIM_ASSERTED = "asserted"


class Rail(str, Enum):
    SAFE = "SAFE"
    NORMAL = "NORMAL"
    EXPRESS = "EXPRESS"


class RiskLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class CognitionStep(str, Enum):
    ANALYZE = "ANALYZE"
    PLAN = "PLAN"
    TOOLS = "TOOLS"
    DRAFT = "DRAFT"
    CRITIQUE = "CRITIQUE"
    FINAL = "FINAL"
    PLAN_TOOLS = "PLAN_TOOLS"


class ModelTier(str, Enum):
    TINY = "tiny"
    MID = "mid"
    BIG = "big"


class CacheMode(str, Enum):
    OFF = "off"
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"


class SpeculationLevel(str, Enum):
    OFF = "off"
    LIGHT = "light"
    AGGRESSIVE = "aggressive"


RAIL_ORDER: dict[Rail, int] = {Rail.SAFE: 0, Rail.NORMAL: 1, Rail.EXPRESS: 2}

RAIL_STEP_CHAINS: dict[Rail, list[str]] = {
    Rail.SAFE: [s.value for s in (
        CognitionStep.ANALYZE,
        CognitionStep.PLAN,
        CognitionStep.TOOLS,
        CognitionStep.DRAFT,
        CognitionStep.CRITIQUE,
        CognitionStep.FINAL,
    )],
    Rail.NORMAL: [s.value for s in (
        CognitionStep.PLAN,
        CognitionStep.TOOLS,
        CognitionStep.DRAFT,
        CognitionStep.FINAL,
    )],
    Rail.EXPRESS: [CognitionStep.PLAN_TOOLS.value, CognitionStep.FINAL.value],
}

CACHE_MODES: tuple[str, ...] = ("off", "L0", "L1", "L2")
CACHE_ORDER: dict[str, int] = {m: i for i, m in enumerate(CACHE_MODES)}

HIGH_RISK_SIGNALS = frozenset({
    "pii",
    "credentials",
    "secrets",
    "constitutional",
    "prod_mutation",
})

SIDE_EFFECT_TOOL_INTENTS = frozenset({
    "write",
    "deploy",
    "exec",
    "apply_patch",
    "mutate",
})


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def cap_rail_at_ceiling(rail: Rail, ceiling: Rail) -> Rail:
    if RAIL_ORDER[rail] > RAIL_ORDER[ceiling]:
        return ceiling
    return rail


def cap_cache_mode(mode: str, ceiling: str | None) -> str:
    if not ceiling:
        return mode
    if CACHE_ORDER[mode] > CACHE_ORDER.get(ceiling, len(CACHE_MODES)):
        return ceiling
    return mode


@dataclass
class PerformanceProfile:
    latency_bias: float = 0.4
    throughput_bias: float = 0.3
    intelligence_bias: float = 0.3
    wL_express_threshold: float = 100.0
    wL_express_floor: float = 50.0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> PerformanceProfile:
        data = dict(data or {})
        return cls(
            latency_bias=float(data.get("latency_bias", 0.4)),
            throughput_bias=float(data.get("throughput_bias", 0.3)),
            intelligence_bias=float(data.get("intelligence_bias", 0.3)),
            wL_express_threshold=float(data.get("wL_express_threshold", 100)),
            wL_express_floor=float(data.get("wL_express_floor", 50)),
        )


@dataclass
class GovernanceWeight:
    wL: float
    wT: float | None = None
    wI: float | None = None
    tier: str | None = None

    @property
    def effective_wT(self) -> float:
        return self.wT if self.wT is not None else self.wL

    @property
    def effective_wI(self) -> float:
        return self.wI if self.wI is not None else self.wL

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> GovernanceWeight:
        data = dict(data or {})
        return cls(
            wL=float(data.get("wL", 0)),
            wT=data.get("wT"),
            wI=data.get("wI"),
            tier=data.get("tier"),
        )


@dataclass
class LawEnvelope:
    law_id: str
    law_version: str
    forbid_express: bool = False
    forbid_cache_above: str | None = None
    forbid_speculation: bool = False
    required_proof: bool = False
    signals: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> LawEnvelope:
        data = dict(data or {})
        return cls(
            law_id=str(data.get("law_id") or "unknown"),
            law_version=str(data.get("law_version") or "unknown"),
            forbid_express=bool(data.get("forbid_express")),
            forbid_cache_above=data.get("forbid_cache_above"),
            forbid_speculation=bool(data.get("forbid_speculation")),
            required_proof=bool(data.get("required_proof")),
            signals=[str(s) for s in (data.get("signals") or [])],
        )


@dataclass
class TaskSignature:
    task_id: str
    pattern_class: str
    mutation_scope: str
    domain: str | None = None
    normalized_prompt_hash: str | None = None
    tool_intents: list[str] = field(default_factory=list)
    context_text: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> TaskSignature:
        data = dict(data or {})
        return cls(
            task_id=str(data.get("task_id") or "task-unknown"),
            pattern_class=str(data.get("pattern_class") or "unknown"),
            mutation_scope=str(data.get("mutation_scope") or "none"),
            domain=data.get("domain"),
            normalized_prompt_hash=data.get("normalized_prompt_hash"),
            tool_intents=[str(t) for t in (data.get("tool_intents") or [])],
            context_text=data.get("context_text"),
        )


@dataclass
class ClusterState:
    load: str = "low"
    hot_domains: list[str] = field(default_factory=list)
    model_availability: dict[str, bool] = field(default_factory=lambda: {
        "tiny": True,
        "mid": True,
        "big": True,
    })

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ClusterState:
        data = dict(data or {})
        return cls(
            load=str(data.get("load") or "low"),
            hot_domains=[str(d) for d in (data.get("hot_domains") or [])],
            model_availability=dict(data.get("model_availability") or {
                "tiny": True,
                "mid": True,
                "big": True,
            }),
        )


@dataclass
class RailDecision:
    task_id: str
    rail: Rail
    risk: RiskLevel
    novelty: RiskLevel
    rationale_codes: list[str]
    law_ceiling: Rail
    contract_version: str = CONTRACT_VERSION
    claim_status: str = CLAIM_ASSERTED
    decided_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["rail"] = self.rail.value
        payload["risk"] = self.risk.value
        payload["novelty"] = self.novelty.value
        payload["law_ceiling"] = self.law_ceiling.value
        return payload


@dataclass
class CognitionPlan:
    task_id: str
    rail: Rail
    steps: list[str]
    model_tier: str
    parallelism: int
    cache_mode: str
    speculation: str
    domain_template: str | None = None
    contract_version: str = CONTRACT_VERSION
    claim_status: str = CLAIM_ASSERTED

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["rail"] = self.rail.value
        return payload
