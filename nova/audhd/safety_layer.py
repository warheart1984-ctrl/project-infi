from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


InteractionMode = Literal["low_stim", "normal", "high_focus"]


@dataclass
class SafetyProfile:
    mode: InteractionMode
    max_tokens: int
    max_topics: int
    require_summaries: bool
    require_check_ins: bool


DEFAULT_LOW_STIM = SafetyProfile(
    mode="low_stim",
    max_tokens=400,
    max_topics=1,
    require_summaries=True,
    require_check_ins=True,
)


@dataclass
class SafetyState:
    overload_score: float = 0.0
    last_topics: list[str] = field(default_factory=list)
    last_summary: str | None = None


class AuDHDCognitiveSafetyLayer:
    OVERLOAD_CHUNK_THRESHOLD = 0.5
    OVERLOAD_REDUCE_THRESHOLD = 0.8
    MAX_REPLY_TOKENS_UNDER_OVERLOAD = 300

    def __init__(self, profile: SafetyProfile | None = None) -> None:
        self.profile = profile or DEFAULT_LOW_STIM
        self.state = SafetyState()

    def before_reply(self, user_text: str) -> None:
        length_factor = min(len(user_text) / 500.0, 1.0)
        self.state.overload_score = max(self.state.overload_score * 0.5, length_factor)

    def should_chunk(self) -> bool:
        return self.state.overload_score > self.OVERLOAD_CHUNK_THRESHOLD

    def should_reduce_output(self) -> bool:
        return self.state.overload_score >= self.OVERLOAD_REDUCE_THRESHOLD

    def max_reply_chars(self) -> int:
        if self.should_reduce_output():
            return self.MAX_REPLY_TOKENS_UNDER_OVERLOAD
        return self.profile.max_tokens

    def scaffold_reply(self, reply: str, *, for_external: bool = False) -> str:
        suffix = ""
        if not for_external:
            if self.profile.require_summaries:
                suffix += "\n\nSummary: (short, concrete recap above)"
            if self.profile.require_check_ins:
                suffix += "\n\nDoes this feel like too much at once, or is this pace okay?"

        text = reply
        if self.should_chunk() or self.should_reduce_output():
            budget = self.max_reply_chars()
            if suffix:
                budget = max(0, budget - len(suffix))
            text = text[:budget]

        if for_external:
            return text
        return text + suffix
