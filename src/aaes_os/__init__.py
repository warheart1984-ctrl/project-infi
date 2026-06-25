"""AAES-OS: governed cognitive execution substrate (RFC v1.0 spine + architecture layer)."""

from __future__ import annotations

from src.aaes_os.action import governed_action
from src.aaes_os.continuity_execution import (
    ContinuityExecutionCheck,
    attach_continuity_execution,
    evaluate_continuity_execution,
)
from src.aaes_os.errors import AaesOsValidationError
from src.aaes_os.governed_span import GovernedSpan
from src.aaes_os.invariant_engine import AaesInvariantEngine, InvariantEngine
from src.aaes_os.models import AuthEnvelope, ReconstructedSpan, RuntimeContext, TraceEvent
from src.aaes_os.modules.daniel import DanielExecutionModule, DanielModule, ModuleRegistry
from src.aaes_os.orchestrator import CognitiveOrchestrator
from src.aaes_os.pipeline_types import (
    AAESAction,
    AAESContext,
    AAESDecision,
    AAESExecuteResult,
    AAESRequest,
    AAESStep,
    AAESStepType,
    PolicyVerdict,
)
from src.aaes_os.policy_engine import PolicyEngine
from src.aaes_os.reconstruct import reconstruct_span
from src.aaes_os.trace_bus import TraceBusValidator
from src.aaes_os.trace_store import TraceStore
from src.aaes_os.types import EventType, InvariantId, Role, SpanState, StepType
from src.aaes_os.uls import UnifiedLanguageSurface, UnifiedLinguisticSurface

__all__ = [
    "AAESAction",
    "AAESContext",
    "AAESDecision",
    "AAESExecuteResult",
    "AAESRequest",
    "AAESStep",
    "AAESStepType",
    "AaesInvariantEngine",
    "AaesOsValidationError",
    "AuthEnvelope",
    "CognitiveOrchestrator",
    "ContinuityExecutionCheck",
    "DanielExecutionModule",
    "DanielModule",
    "EventType",
    "GovernedSpan",
    "InvariantEngine",
    "InvariantId",
    "ModuleRegistry",
    "PolicyEngine",
    "PolicyVerdict",
    "ReconstructedSpan",
    "Role",
    "RuntimeContext",
    "SpanState",
    "StepType",
    "TraceBusValidator",
    "TraceEvent",
    "TraceStore",
    "UnifiedLanguageSurface",
    "UnifiedLinguisticSurface",
    "attach_continuity_execution",
    "evaluate_continuity_execution",
    "governed_action",
    "reconstruct_span",
]
