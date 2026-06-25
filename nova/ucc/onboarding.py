"""UCC user onboarding flow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from nova.ucc.patterns import SAFE_OPENING, pacing_consent_prompt


CognitiveStyle = Literal["linear", "audhd", "mixed"]


@dataclass
class OnboardingState:
    pacing_mode: str | None = None
    structure_mode: str | None = None
    cognitive_style: CognitiveStyle | None = None
    safety_contract_accepted: bool = False


class UCCOnboardingFlow:
    STEPS = [
        "gentle_orientation",
        "pacing_choice",
        "structure_choice",
        "cognitive_style_detection",
        "safety_contract",
    ]

    def gentle_orientation(self) -> str:
        return "Hey. You don't need to organize anything. I'll match your pace."

    def pacing_choice(self) -> str:
        return pacing_consent_prompt()

    def structure_choice(self) -> str:
        return "How do you want me to shape things: summary, steps, or deeper dive."

    def cognitive_style_detection(self) -> str:
        return (
            "Do you prefer:\n"
            "- structured, step-by-step logic\n"
            "- flexible, explicit, sensory-safe scaffolding\n"
            "- or a mix of both"
        )

    def safety_contract(self) -> str:
        return "If anything feels like too much, say 'pause' and I'll slow down."

    def full_intro(self) -> str:
        return "\n\n".join(
            [
                self.gentle_orientation(),
                SAFE_OPENING.template,
                self.cognitive_style_detection(),
                self.safety_contract(),
            ]
        )
