from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LearningArc:
    id: str
    topic: str
    milestones: list[str] = field(default_factory=list)
    completed: list[str] = field(default_factory=list)


class AuDHDLearningEnvironment:
    def __init__(self) -> None:
        self.arcs: dict[str, LearningArc] = {}

    def start_arc(self, topic: str) -> LearningArc:
        arc = LearningArc(id=f"arc:{len(self.arcs)}", topic=topic)
        self.arcs[arc.id] = arc
        return arc

    def add_milestone(self, arc_id: str, milestone: str) -> None:
        self.arcs[arc_id].milestones.append(milestone)

    def complete_milestone(self, arc_id: str, milestone: str) -> None:
        arc = self.arcs[arc_id]
        if milestone in arc.milestones and milestone not in arc.completed:
            arc.completed.append(milestone)
