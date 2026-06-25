"""Constitutional core — CSR primitives, articles, and registry."""

from constitutional.core.amendment import (
    AmendmentChangeType,
    AmendmentContext,
    AmendmentEngine,
)
from constitutional.core.articles import (
    ARTICLE_R,
    ARTICLE_S,
    ARTICLE_S_ID,
    ARTICLE_S_INVARIANT,
    ARTICLE_S_REFERENCE,
    FOUNDER_DEPENDENCY_BLOCK_THRESHOLD,
    MISSION_MAX_FOUNDER_DEPENDENCY,
    MISSION_MIN_SURVIVABILITY,
    RECONSTRUCTABILITY_INVARIANT,
    SUCCESSION_MIN_STEWARD_INDEPENDENCE,
    SUCCESSION_MIN_SURVIVABILITY,
    SURVIVABILITY_BLOCK_THRESHOLD,
    SURVIVABILITY_WARN_THRESHOLD,
)
from constitutional.core.graph import DOMAIN_STATE_MAPS, LEGAL_TRANSITIONS, validate_transition
from constitutional.core.ledger import TransitionLedger
from constitutional.core.models import StateName, StateObject, Transition
from constitutional.core.observer import ObserverVerificationEngine, ObserverVerificationResult
from constitutional.core.registry import ConstitutionalRegistry, constitutional_registry
from constitutional.core.runtime import ConstitutionalStateRuntime

StateTransition = Transition

__all__ = [
    "ARTICLE_R",
    "ARTICLE_S",
    "ARTICLE_S_ID",
    "ARTICLE_S_INVARIANT",
    "ARTICLE_S_REFERENCE",
    "AmendmentChangeType",
    "AmendmentContext",
    "AmendmentEngine",
    "ConstitutionalRegistry",
    "ConstitutionalStateRuntime",
    "DOMAIN_STATE_MAPS",
    "FOUNDER_DEPENDENCY_BLOCK_THRESHOLD",
    "LEGAL_TRANSITIONS",
    "MISSION_MAX_FOUNDER_DEPENDENCY",
    "MISSION_MIN_SURVIVABILITY",
    "ObserverVerificationEngine",
    "ObserverVerificationResult",
    "RECONSTRUCTABILITY_INVARIANT",
    "StateName",
    "StateObject",
    "StateTransition",
    "SUCCESSION_MIN_STEWARD_INDEPENDENCE",
    "SUCCESSION_MIN_SURVIVABILITY",
    "SURVIVABILITY_BLOCK_THRESHOLD",
    "SURVIVABILITY_WARN_THRESHOLD",
    "Transition",
    "TransitionLedger",
    "constitutional_registry",
    "validate_transition",
]
