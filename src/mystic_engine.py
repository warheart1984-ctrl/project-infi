"""Jarvis-native Mystic reflection engine."""

from __future__ import annotations

from dataclasses import dataclass
import re


STATE_ORDER = (
    "lost",
    "burdened",
    "seeking",
    "struggling",
    "awakening",
    "building",
    "transforming",
    "steady",
)

ARCHETYPE_LABELS = {
    "hero": "Hero",
    "shadow": "Shadow",
    "guide": "Guide",
    "builder": "Builder",
    "trickster": "Trickster",
    "witness": "Witness",
}

STATE_LABELS = {
    "lost": "Lost",
    "burdened": "Burdened",
    "seeking": "Seeking",
    "struggling": "Struggling",
    "awakening": "Awakening",
    "building": "Building",
    "transforming": "Transforming",
    "steady": "Steady",
}

STATE_HINTS = {
    "lost": (
        "lost",
        "stuck",
        "nothing is moving",
        "nothing works",
        "numb",
        "empty",
        "directionless",
    ),
    "burdened": (
        "burdened",
        "guilt",
        "ashamed",
        "shame",
        "regret",
        "barely",
        "heavy",
        "weight",
    ),
    "struggling": (
        "survive",
        "survival",
        "collapse",
        "overwhelmed",
        "exhausted",
        "burned out",
        "breaking",
        "fight just to",
    ),
    "awakening": (
        "awakening",
        "idea",
        "breakthrough",
        "vision",
        "change everything",
        "wake up",
        "clarity",
    ),
    "building": (
        "build",
        "building",
        "system",
        "routine",
        "structure",
        "ship",
        "project",
        "discipline",
    ),
    "transforming": (
        "transform",
        "transformation",
        "reaction",
        "control",
        "anger",
        "rage",
        "pause",
        "choose differently",
    ),
    "steady": (
        "steady",
        "stable",
        "consistent",
        "holding the line",
        "maintain",
        "maintenance",
        "track one win",
    ),
}

TRIGGER_TERMS = ("mystic", "mythic")
REQUEST_TERMS = (
    "reading",
    "archetype",
    "current state",
    "next move",
    "next action",
    "read me",
    "interpret",
)

PREFIX_PATTERNS = (
    "mystic reading",
    "mythic reading",
    "use mystic",
    "use mythic",
    "read me mythically",
    "read me mystically",
)


def _humanize(value: str | None) -> str:
    return STATE_LABELS.get(value or "", ARCHETYPE_LABELS.get(value or "", str(value or "").replace("_", " ").title()))


@dataclass(slots=True)
class MysticReading:
    input_text: str
    state: str
    dominant_archetype: str
    opposing_archetype: str
    trial: str
    next_action: str
    meaning: str
    risk: str
    detected_signals: list[str]

    def to_dict(self) -> dict:
        return {
            "input_text": self.input_text,
            "state": self.state,
            "state_label": _humanize(self.state),
            "dominant_archetype": self.dominant_archetype,
            "dominant_archetype_label": _humanize(self.dominant_archetype),
            "opposing_archetype": self.opposing_archetype,
            "opposing_archetype_label": _humanize(self.opposing_archetype),
            "trial": self.trial,
            "next_action": self.next_action,
            "meaning": self.meaning,
            "risk": self.risk,
            "detected_signals": list(self.detected_signals),
        }


def extract_mystic_prompt(text: str | None) -> str | None:
    """Return the user payload for an explicit Mystic/Mythic reading request."""
    cleaned = " ".join(str(text or "").split()).strip()
    if not cleaned:
        return None

    lower = cleaned.lower()
    if not any(term in lower for term in TRIGGER_TERMS):
        return None

    for prefix in PREFIX_PATTERNS:
        if lower.startswith(prefix):
            remainder = cleaned[len(prefix) :].lstrip(" :,-")
            return remainder or cleaned

    if any(term in lower for term in REQUEST_TERMS):
        stripped = re.sub(r"\b(mystic|mythic)\b", "", cleaned, flags=re.IGNORECASE)
        stripped = re.sub(r"\b(reading|interpretation)\b", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(
            r"^(give me|show me|offer me|run|use|do)\s+(a\s+|an\s+|the\s+)?",
            "",
            stripped,
            flags=re.IGNORECASE,
        )
        stripped = " ".join(stripped.split()).strip(" :,-")
        return stripped or cleaned

    return None


class MysticEngine:
    """Deterministic archetype/state reader ported from the Mystic sidecar app."""

    def detect_state(self, input_text: str) -> tuple[str, list[str]]:
        lower = " ".join(str(input_text or "").lower().split())
        scores = {state: 0 for state in STATE_ORDER}
        matched_signals: list[str] = []

        for state, hints in STATE_HINTS.items():
            for hint in hints:
                if hint in lower:
                    scores[state] += 1
                    if hint not in matched_signals:
                        matched_signals.append(hint)

        best_state = max(STATE_ORDER, key=lambda state: scores[state])
        if scores[best_state] <= 0:
            return "seeking", []
        return best_state, matched_signals

    def assign_archetypes(self, state: str) -> tuple[str, str]:
        if state == "lost":
            return "shadow", "guide"
        if state == "burdened":
            return "shadow", "builder"
        if state == "struggling":
            return "hero", "shadow"
        if state == "awakening":
            return "guide", "trickster"
        if state == "building":
            return "builder", "shadow"
        if state == "transforming":
            return "hero", "shadow"
        if state == "steady":
            return "builder", "trickster"
        return "witness", "trickster"

    def generate_trial(self, state: str) -> str:
        if state == "lost":
            return "Meaning vs numbness"
        if state == "burdened":
            return "Guilt vs understanding"
        if state == "struggling":
            return "Survival vs collapse"
        if state == "awakening":
            return "Vision vs distraction"
        if state == "building":
            return "Discipline vs inconsistency"
        if state == "transforming":
            return "Reaction vs control"
        if state == "steady":
            return "Maintenance vs drift"
        return "Action vs avoidance"

    def suggest_next_action(self, state: str) -> str:
        if state == "lost":
            return "Complete one grounding action in the next hour."
        if state == "burdened":
            return "Name the guilt clearly and replace self-attack with one honest sentence."
        if state == "struggling":
            return "Do one survival action now: water, food, walk, or rest."
        if state == "awakening":
            return "Write the idea clearly in five sentences."
        if state == "building":
            return "Finish one concrete system task today."
        if state == "transforming":
            return "Pause for 10 seconds before acting when anger rises."
        if state == "steady":
            return "Reinforce your daily protocol and track one win before bed."
        return "Choose one small action and complete it fully."

    def build_meaning(self, state: str, trial: str) -> str:
        if state == "transforming":
            return "You are replacing reaction with deliberate choice."
        if state == "steady":
            return "The work now is maintenance with awareness, not dramatic reinvention."
        if state == "awakening":
            return "Something new is trying to take form, but it still needs structure."
        return f"Your current path is {trial.lower()}."

    def build_risk(self, state: str) -> str:
        if state == "transforming":
            return "Ignoring the pause can reactivate regret loops."
        if state == "steady":
            return "Drift usually returns quietly through skipped rituals and small neglect."
        return "Inaction reinforces the current negative pattern."

    def read(self, input_text: str) -> dict:
        cleaned = " ".join(str(input_text or "").split()).strip()
        state, signals = self.detect_state(cleaned)
        dominant_archetype, opposing_archetype = self.assign_archetypes(state)
        trial = self.generate_trial(state)
        next_action = self.suggest_next_action(state)
        reading = MysticReading(
            input_text=cleaned,
            state=state,
            dominant_archetype=dominant_archetype,
            opposing_archetype=opposing_archetype,
            trial=trial,
            next_action=next_action,
            meaning=self.build_meaning(state, trial),
            risk=self.build_risk(state),
            detected_signals=signals,
        )
        from src.aais_ul_substrate import wrap_runtime_snapshot

        return wrap_runtime_snapshot(reading.to_dict())


mystic_engine = MysticEngine()
