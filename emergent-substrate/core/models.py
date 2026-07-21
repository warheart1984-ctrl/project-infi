"""
Core Models - Pydantic v2 Data Contracts
18 models, 5 enums
"""

from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class PacketType(str, Enum):
    """Types of entropy packets Jon can emit"""
    IDEA = "idea"
    FEELING = "feeling"
    METAPHOR = "metaphor"
    CHALLENGE = "challenge"
    EXTENSION = "extension"
    MUTATION = "mutation"


class EmotionalTone(str, Enum):
    """Emotional tones for entropy packets"""
    CURIOUS = "curious"
    EXCITED = "excited"
    CONTEMPLATIVE = "contemplative"
    PLAYFUL = "playful"
    SERIOUS = "serious"
    MELANCHOLIC = "melancholic"
    HOPEFUL = "hopeful"
    FRUSTRATED = "frustrated"
    NEUTRAL = "neutral"


class GovernanceStatus(str, Enum):
    """Governance validation results"""
    PASS = "pass"
    WARN = "warn"
    BLOCK = "block"


class EntropyPacket(BaseModel):
    """Raw entropy packet emitted by Jon"""
    packet_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    packet_type: PacketType
    raw_content: str
    emotional_tone: EmotionalTone
    cross_domain: List[str] = Field(default_factory=list)
    intensity: float = Field(ge=0.0, le=1.0, default=0.5)
    tags: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('intensity')
    @classmethod
    def validate_intensity(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError('Intensity must be between 0.0 and 1.0')
        return v


class StructuredModel(BaseModel):
    """Pre-governance shaped output from OrderEngine.shape()"""
    model_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_packet_id: str
    title: str
    abstract: str
    invariants: List[str] = Field(default_factory=list)
    cross_domain_decomposition: Dict[str, List[str]] = Field(default_factory=dict)
    constraints: List[str] = Field(default_factory=list)
    structure_type: str = "generic"
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    raw_model: Optional[Dict[str, Any]] = None


class ValidationResult(BaseModel):
    """Result of governance validation"""
    constitution_name: str
    constitution_version: str
    priority: int
    status: GovernanceStatus
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GovernedSpec(BaseModel):
    """Post-governance final artifact"""
    spec_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_model_id: str
    title: str
    content: str
    validation_results: List[ValidationResult] = Field(default_factory=list)
    governance_status: GovernanceStatus
    integrated: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IdentityMemory(BaseModel):
    """Key-value identity memory"""
    key: str
    value: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class ContinuityMemory(BaseModel):
    """Goals, active projects, constitution IDs"""
    goal: str
    active_projects: List[str] = Field(default_factory=list)
    attached_constitutions: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class EvolutionEvent(BaseModel):
    """Append-only ledger entry - substrate's living history"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str  # "packet_emitted", "spec_integrated", "constitution_attached", etc.
    description: str
    related_ids: List[str] = Field(default_factory=list)  # packet_ids, spec_ids, etc.
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConstitutionHook(BaseModel):
    """Registry entry for attached constitution"""
    constitution_name: str
    constitution_version: str
    priority: int
    attached_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True


class SubstrateState(BaseModel):
    """Session snapshot of substrate state"""
    state_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    iteration: int = 0
    is_alive: bool = False
    total_packets_emitted: int = 0
    total_specs_produced: int = 0
    total_constitutions_attached: int = 0
    total_loop_iterations: int = 0
    identity_memory_non_empty: bool = False
    last_activity: Optional[datetime] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def check_alive(self) -> bool:
        """
        Execution Contract - state.is_alive() is True when:
        - At least one entropy packet emitted
        - At least one governed spec produced
        - At least one constitution attached
        - At least one full loop iteration completed
        - Identity memory is non-empty
        """
        return (
            self.total_packets_emitted > 0 and
            self.total_specs_produced > 0 and
            self.total_constitutions_attached > 0 and
            self.total_loop_iterations > 0 and
            self.identity_memory_non_empty
        )


class FeedbackHook(BaseModel):
    """Optional feedback hook for Jon to react to"""
    hook_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trigger_condition: str
    response_type: str  # "challenge", "extension", "mutation"
    active: bool = True


class Constitution(BaseModel):
    """Base constitution interface"""
    name: str
    version: str
    priority: int

    def validate(self, model: StructuredModel) -> ValidationResult:
        """Validate a structured model against this constitution"""
        raise NotImplementedError("Subclasses must implement validate()")
