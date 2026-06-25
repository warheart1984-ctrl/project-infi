"""Unified Cognitive Compatibility (UCC) layer."""

from nova.ucc.onboarding import OnboardingState, UCCOnboardingFlow
from nova.ucc.patterns import PATTERNS, pacing_consent_prompt, render_pattern, requires_pacing_consent
from nova.ucc.pit import enrich_pit2_ucc, enrich_pit3_ucc, ucc_enabled

__all__ = [
    "OnboardingState",
    "PATTERNS",
    "UCCOnboardingFlow",
    "enrich_pit2_ucc",
    "enrich_pit3_ucc",
    "pacing_consent_prompt",
    "render_pattern",
    "requires_pacing_consent",
    "ucc_enabled",
]
