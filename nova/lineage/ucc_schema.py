from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


PacingMode = Literal["slow", "steady", "fast"]
StructureMode = Literal["summary", "steps", "deep_dive"]
CognitiveStyle = Literal["linear", "audhd", "mixed"]


@dataclass
class UCCContext:
    cognitive_style: CognitiveStyle | None = None
    pacing_mode: PacingMode | None = None
    structure_mode: StructureMode | None = None
    overload_score: float | None = None
    protection_flags: dict[str, bool] | None = None
    interpreter_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "cognitive_style": self.cognitive_style,
            "pacing_mode": self.pacing_mode,
            "structure_mode": self.structure_mode,
            "overload_score": self.overload_score,
            "protection_flags": dict(self.protection_flags or {}),
            "interpreter_used": self.interpreter_used,
        }


@dataclass
class UCCLineageEvent:
    id: str
    kind: str
    actor_id: str
    intent_id: str | None
    ucc: UCCContext
    timestamp: str
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "actor_id": self.actor_id,
            "intent_id": self.intent_id,
            "ucc": self.ucc.to_dict(),
            "timestamp": self.timestamp,
            "extra": dict(self.extra),
        }
