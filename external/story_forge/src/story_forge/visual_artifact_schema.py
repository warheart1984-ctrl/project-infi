from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_token(value: str) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def unique_tokens(values: list[str] | tuple[str, ...] | None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values or []:
        token = normalize_token(value)
        if not token or token in seen:
            continue
        seen.add(token)
        ordered.append(token)
    return ordered


def unique_strings(values: list[str] | tuple[str, ...] | None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values or []:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def merge_unique(*groups: list[str] | tuple[str, ...]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        merged.extend(group)
    return unique_strings(merged)


def apply_hook_updates(
    hooks: list[str],
    updates: dict[str, str] | None,
) -> list[str]:
    if not updates:
        return unique_tokens(hooks)
    normalized = unique_tokens(hooks)
    for source, target in updates.items():
        source_token = normalize_token(source)
        target_token = normalize_token(target)
        if source_token and source_token in normalized:
            normalized = [hook for hook in normalized if hook != source_token]
        if target_token and target_token not in normalized:
            normalized.append(target_token)
    return normalized


@dataclass(slots=True)
class ImageArtifactRecord:
    artifact_id: str
    timestamp: str = field(default_factory=utc_now_iso)
    cartridge_id: str = "default"
    scene_id: str = ""
    event_type: str = ""
    character_ids: list[str] = field(default_factory=list)
    location: str = ""
    symbols: list[str] = field(default_factory=list)
    visual_tags: list[str] = field(default_factory=list)
    continuity_hooks: list[str] = field(default_factory=list)
    tone_profile: str = ""
    narrative_arc: str = ""
    major: bool = False
    image_path: str = ""
    metadata_path: str = ""

    def __post_init__(self) -> None:
        self.cartridge_id = str(self.cartridge_id or "default").strip() or "default"
        self.scene_id = str(self.scene_id or "").strip()
        self.event_type = normalize_token(self.event_type) or "scene"
        self.character_ids = unique_tokens(self.character_ids)
        self.location = normalize_token(self.location)
        self.symbols = unique_tokens(self.symbols)
        self.visual_tags = unique_tokens(self.visual_tags)
        self.continuity_hooks = unique_tokens(self.continuity_hooks)
        self.tone_profile = normalize_token(self.tone_profile)
        self.narrative_arc = normalize_token(self.narrative_arc)
        self.major = bool(self.major)
        self.image_path = str(self.image_path or "").strip()
        self.metadata_path = str(self.metadata_path or "").strip()


@dataclass(slots=True)
class PendingVisualContext:
    artifact_ids: list[str] = field(default_factory=list)
    continuity_hooks: list[str] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)
    match_reasons: list[str] = field(default_factory=list)
    context: str = ""
    narrative_arc: str = ""
    location: str = ""
    character_ids: list[str] = field(default_factory=list)
    updated_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        self.artifact_ids = unique_strings(self.artifact_ids)
        self.continuity_hooks = unique_tokens(self.continuity_hooks)
        self.symbols = unique_tokens(self.symbols)
        self.match_reasons = unique_strings(self.match_reasons)
        self.context = str(self.context or "").strip()
        self.narrative_arc = normalize_token(self.narrative_arc)
        self.location = normalize_token(self.location)
        self.character_ids = unique_tokens(self.character_ids)


@dataclass(slots=True)
class VisualMemoryState:
    artifact_ids: list[str] = field(default_factory=list)
    hook_state: dict[str, str] = field(default_factory=dict)
    pending_context: PendingVisualContext | None = None
    last_recall_artifact_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.artifact_ids = unique_strings(self.artifact_ids)
        self.hook_state = {
            normalize_token(hook): str(artifact_id).strip()
            for hook, artifact_id in self.hook_state.items()
            if normalize_token(hook) and str(artifact_id).strip()
        }
        if self.pending_context is not None and not isinstance(self.pending_context, PendingVisualContext):
            self.pending_context = PendingVisualContext(**dict(self.pending_context))
        self.last_recall_artifact_ids = unique_strings(self.last_recall_artifact_ids)


@dataclass(slots=True)
class VisualSceneContext:
    cartridge_id: str
    scene_id: str
    event_type: str
    character_ids: list[str] = field(default_factory=list)
    location: str = ""
    symbols: list[str] = field(default_factory=list)
    visual_tags: list[str] = field(default_factory=list)
    continuity_hooks: list[str] = field(default_factory=list)
    tone_profile: str = ""
    narrative_arc: str = ""
    major: bool = False
    force_image_event: bool = False
    source_image_path: str = ""
    continuity_hook_updates: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.cartridge_id = str(self.cartridge_id or "default").strip() or "default"
        self.scene_id = str(self.scene_id or "").strip()
        self.event_type = normalize_token(self.event_type) or "scene"
        self.character_ids = unique_tokens(self.character_ids)
        self.location = normalize_token(self.location)
        self.symbols = unique_tokens(self.symbols)
        self.visual_tags = unique_tokens(self.visual_tags)
        self.continuity_hooks = unique_tokens(self.continuity_hooks)
        self.tone_profile = normalize_token(self.tone_profile)
        self.narrative_arc = normalize_token(self.narrative_arc)
        self.major = bool(self.major)
        self.force_image_event = bool(self.force_image_event)
        self.source_image_path = str(self.source_image_path or "").strip()
        self.continuity_hook_updates = {
            normalize_token(source): normalize_token(target)
            for source, target in self.continuity_hook_updates.items()
            if normalize_token(source) and normalize_token(target)
        }


@dataclass(slots=True)
class VisualRecallResult:
    triggered: bool = False
    artifacts: list[ImageArtifactRecord] = field(default_factory=list)
    continuity_hooks: list[str] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)
    match_reasons: list[str] = field(default_factory=list)
    context: str = ""

    def __post_init__(self) -> None:
        self.continuity_hooks = unique_tokens(self.continuity_hooks)
        self.symbols = unique_tokens(self.symbols)
        self.match_reasons = unique_strings(self.match_reasons)
        self.context = str(self.context or "").strip()

    @property
    def artifact_ids(self) -> list[str]:
        return unique_strings([artifact.artifact_id for artifact in self.artifacts if artifact.artifact_id])
