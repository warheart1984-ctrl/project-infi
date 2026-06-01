from __future__ import annotations

from dataclasses import dataclass, field

from story_forge.contracts.pipeline import TARGET_GAME


@dataclass(slots=True)
class SceneUnit:
    scene_id: str
    title: str
    summary: str
    source_span: str = ""
    emotional_tags: list[str] = field(default_factory=list)
    structural_markers: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Act:
    act_id: str
    title: str
    scenes: list[SceneUnit] = field(default_factory=list)


@dataclass(slots=True)
class TranslationLaneInput:
    raw_text: str
    title: str
    target: str = TARGET_GAME


@dataclass(slots=True)
class SceneGrammar:
    title: str
    acts: list[Act] = field(default_factory=list)
    total_scenes: int = 0
    emotional_tags: list[str] = field(default_factory=list)
    structural_markers: list[str] = field(default_factory=list)
    implemented: bool = False
    valid: bool = True
