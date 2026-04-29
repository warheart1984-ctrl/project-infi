from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from story_forge.contracts.engine_handoff import EngineHandoffInput
from story_forge.models import make_id, utc_now


@dataclass(slots=True)
class BackendImportScene:
    scene_id: str
    title: str
    summary: str
    act_id: str
    order_index: int

    def to_payload(self) -> dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "title": self.title,
            "summary": self.summary,
            "act_id": self.act_id,
            "order_index": self.order_index,
        }


@dataclass(slots=True)
class BackendImportArtifact:
    import_id: str
    session_id: str
    title: str
    target: str
    source_mode: str
    source_path: str
    imported_at: str
    scene_count: int
    output_format: str
    lumen_mode: str
    directional_priorities: list[str] = field(default_factory=list)
    directional_constraints: list[str] = field(default_factory=list)
    scenes: list[BackendImportScene] = field(default_factory=list)
    transitions: list[dict[str, str]] = field(default_factory=list)
    presented_text: str = ""
    cinematic: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "import_id": self.import_id,
            "session_id": self.session_id,
            "title": self.title,
            "target": self.target,
            "source_mode": self.source_mode,
            "source_path": self.source_path,
            "imported_at": self.imported_at,
            "scene_count": self.scene_count,
            "output_format": self.output_format,
            "lumen_mode": self.lumen_mode,
            "directional_priorities": list(self.directional_priorities),
            "directional_constraints": list(self.directional_constraints),
            "scenes": [scene.to_payload() for scene in self.scenes],
            "transitions": [dict(transition) for transition in self.transitions],
            "presented_text": self.presented_text,
            "cinematic": dict(self.cinematic) if isinstance(self.cinematic, dict) else None,
        }


def build_backend_import_artifact(
    *,
    session_id: str,
    handoff: EngineHandoffInput,
    source_mode: str,
    source_path: str,
) -> BackendImportArtifact:
    scenes = [
        BackendImportScene(
            scene_id=unit.scene_id,
            title=unit.title,
            summary=unit.summary,
            act_id=unit.act_id,
            order_index=unit.order_index,
        )
        for unit in handoff.staged_plan.staged_units
    ]
    transitions = [
        {
            "from_scene_id": transition.from_scene_id,
            "to_scene_id": transition.to_scene_id,
            "transition_type": transition.transition_type,
            "rationale": transition.rationale,
        }
        for transition in handoff.staged_plan.transitions
    ]
    cinematic = None
    if handoff.cinematic_plan is not None:
        cinematic = {
            "shot_count": len(handoff.cinematic_plan.shots),
            "pacing_rules": list(handoff.cinematic_plan.pacing_rules),
            "continuity_hook_count": len(handoff.cinematic_plan.continuity_hooks),
            "transition_count": len(handoff.cinematic_plan.transitions),
        }
    return BackendImportArtifact(
        import_id=make_id("backend_import"),
        session_id=session_id,
        title=handoff.scene_grammar.title,
        target=handoff.directional_context.target,
        source_mode=source_mode,
        source_path=source_path,
        imported_at=utc_now(),
        scene_count=handoff.scene_grammar.total_scenes,
        output_format=handoff.presented_output.format,
        lumen_mode=handoff.presented_output.lumen_mode,
        directional_priorities=list(handoff.directional_context.priorities),
        directional_constraints=list(handoff.directional_context.constraints),
        scenes=scenes,
        transitions=transitions,
        presented_text=handoff.presented_output.text,
        cinematic=cinematic,
    )
