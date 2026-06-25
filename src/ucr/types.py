"""UCR v0.1 — shared dataclasses for Ultima Cognitive Runtime."""

# Mythic: Ultima Cognitive Runtime ledger types
# Engineering: UcrTypes
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class RiskProfile(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SafetyVerdict(str, Enum):
    SAFE = "safe"
    UNSAFE = "unsafe"


class UcrStage(str, Enum):
    SENSE = "sense"
    CLASSIFY = "classify"
    ACTIVATE = "activate"
    GOVERN = "govern"
    MERGE = "merge"
    COMMIT = "commit"


@dataclass(slots=True)
class CognitiveSituation:
    """Stage 1 output — normalized perceptual frame for one turn."""

    turn_id: str
    raw_input: str
    normalized_input: str
    actor_id: str
    session_id: str | None = None
    intent_hint: str = "execute"
    risk_profile: RiskProfile = RiskProfile.LOW
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.turn_id or "").strip():
            raise ValueError("turn_id is required")
        if not str(self.normalized_input or "").strip():
            raise ValueError("normalized_input is required")
        if not str(self.actor_id or "").strip():
            raise ValueError("actor_id is required")


@dataclass(slots=True)
class CognitiveModeContract:
    """Stage 2 output — mode contract selecting runtime family members."""

    contract_id: str
    mode: str
    required_runtimes: tuple[str, ...]
    optional_runtimes: tuple[str, ...] = ()
    risk_profile: RiskProfile = RiskProfile.LOW
    intent_priority: str = "operator"
    bounds: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.contract_id:
            self.contract_id = f"contract_{uuid4().hex}"
        if not str(self.mode or "").strip():
            raise ValueError("mode is required")
        if not self.required_runtimes:
            raise ValueError("required_runtimes must be non-empty")


@dataclass(slots=True)
class RuntimeConfig:
    """Per-runtime configuration passed at activation."""

    runtime_id: str
    enabled: bool = True
    priority: int = 100
    veto_capable: bool = False
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.runtime_id or "").strip():
            raise ValueError("runtime_id is required")


@dataclass(slots=True)
class RuntimeActivationRecord:
    """One runtime activation in stage 3."""

    runtime_id: str
    accepted: bool
    config: RuntimeConfig
    reason: str = ""
    activated_at_stage: UcrStage = UcrStage.ACTIVATE

    def __post_init__(self) -> None:
        if not str(self.runtime_id or "").strip():
            raise ValueError("runtime_id is required")


@dataclass(slots=True)
class RuntimeOutput:
    """Stage 4 partial output from one cognitive runtime."""

    runtime_id: str
    status: str
    payload: dict[str, Any] = field(default_factory=dict)
    veto: bool = False
    veto_reason: str | None = None

    def __post_init__(self) -> None:
        if not str(self.runtime_id or "").strip():
            raise ValueError("runtime_id is required")
        if not str(self.status or "").strip():
            raise ValueError("status is required")


@dataclass(slots=True)
class RuntimeTrace:
    """Explainability record for one runtime execution."""

    runtime_id: str
    summary: str
    stages: tuple[str, ...] = ()
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.runtime_id or "").strip():
            raise ValueError("runtime_id is required")
        if not str(self.summary or "").strip():
            raise ValueError("summary is required")


@dataclass(slots=True)
class GovernedLedgerEvent:
    """Append-only governed ledger entry."""

    stage: UcrStage
    event_type: str
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = ""

    def __post_init__(self) -> None:
        if not self.event_id:
            self.event_id = f"ucr_evt_{uuid4().hex}"


@dataclass(slots=True)
class UnifiedCognitiveAct:
    """Stage 4 merged governed act before commit."""

    act_id: str
    turn_id: str
    contract_id: str
    status: str
    merged_payload: dict[str, Any] = field(default_factory=dict)
    runtime_outputs: tuple[RuntimeOutput, ...] = ()
    vetoed: bool = False
    veto_reason: str | None = None
    traces: tuple[RuntimeTrace, ...] = ()

    def __post_init__(self) -> None:
        if not self.act_id:
            self.act_id = f"act_{uuid4().hex}"
        if not str(self.turn_id or "").strip():
            raise ValueError("turn_id is required")
        if not str(self.contract_id or "").strip():
            raise ValueError("contract_id is required")


RuntimeActivationLedger = list[RuntimeActivationRecord]
GovernedCognitiveLedger = list[GovernedLedgerEvent]


class LawTier(str, Enum):
    SAFETY = "safety"
    CONSTITUTIONAL = "constitutional"
    ULTIMA = "ultima"
    RUNTIME = "runtime"
    TURN = "turn"


@dataclass(frozen=True, slots=True)
class LawRule:
    """One enforceable rule within a law tier."""

    rule_id: str
    tier: LawTier
    summary: str
    forbidden_markers: tuple[str, ...] = ()
    required_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not str(self.rule_id or "").strip():
            raise ValueError("rule_id is required")
        if not str(self.summary or "").strip():
            raise ValueError("summary is required")


@dataclass(slots=True)
class LawSet:
    """Bounded collection of rules for one lattice tier."""

    tier: LawTier
    rules: tuple[LawRule, ...] = ()

    def rule_ids(self) -> tuple[str, ...]:
        return tuple(rule.rule_id for rule in self.rules)


@dataclass(slots=True)
class DeliberationCandidate:
    """One deliberation option entering merge calculus."""

    candidate_id: str
    label: str
    payload: dict[str, Any] = field(default_factory=dict)
    runtime_id: str = "cognitive.deliberation"
    traceable: bool = True
    bounded: bool = True
    clarity: float = 0.5
    helpfulness: float = 0.5
    risk: float = 0.5
    intent_alignment: float = 0.5

    def __post_init__(self) -> None:
        if not str(self.candidate_id or "").strip():
            raise ValueError("candidate_id is required")
        if not str(self.label or "").strip():
            raise ValueError("label is required")


@dataclass(slots=True)
class MergeInputs:
    """Inputs to merge calculus for one turn."""

    turn_id: str
    contract_id: str
    A_D: tuple[DeliberationCandidate, ...]
    A_M: RuntimeOutput | None = None
    A_S: RuntimeOutput | None = None
    A_So: RuntimeOutput | None = None
    A_E: RuntimeOutput | None = None
    L_C: LawSet | None = None
    L_U: LawSet | None = None
    L_R: dict[str, LawSet] = field(default_factory=dict)
    L_T: CognitiveModeContract | None = None
    scoring_weights: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.turn_id or "").strip():
            raise ValueError("turn_id is required")
        if not str(self.contract_id or "").strip():
            raise ValueError("contract_id is required")


@dataclass(slots=True)
class RefusalAct:
    """Safety-gated refusal — maps to UnifiedCognitiveAct with refused status."""

    turn_id: str
    contract_id: str
    reason: str
    safety_evidence: dict[str, Any] = field(default_factory=dict)
    act_id: str = ""

    def __post_init__(self) -> None:
        if not self.act_id:
            self.act_id = f"refusal_{uuid4().hex}"
        if not str(self.reason or "").strip():
            raise ValueError("reason is required")

    def to_unified_act(self) -> UnifiedCognitiveAct:
        return UnifiedCognitiveAct(
            act_id=self.act_id,
            turn_id=self.turn_id,
            contract_id=self.contract_id,
            status="refused",
            merged_payload={
                "refusal": True,
                "reason": self.reason,
                "safety_evidence": dict(self.safety_evidence),
            },
            vetoed=True,
            veto_reason=self.reason,
        )
