from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Utterance:
    text: str
    tone: str
    intent: str


class AuDHDInterpreter:
    def to_nt(self, utterance: Utterance) -> str:
        if utterance.intent == "boundary":
            return f"I need to set a clear boundary here: {utterance.text}"
        if utterance.intent == "info":
            return f"Just to share information, not criticism: {utterance.text}"
        return utterance.text

    def to_audhd(self, utterance: Utterance) -> str:
        if utterance.intent == "request":
            return f"Request (explicit): {utterance.text}"
        if utterance.intent == "feedback":
            return f"Feedback (not a rejection): {utterance.text}"
        if utterance.intent == "boundary":
            return f"Boundary (explicit): {utterance.text}"
        return f"Message (explicit intent={utterance.intent}): {utterance.text}"

    def has_explicit_intent_label(self, text: str) -> bool:
        markers = ("Request (explicit)", "Feedback (not a rejection)", "Boundary (explicit)", "Message (explicit intent=")
        return any(marker in text for marker in markers)
