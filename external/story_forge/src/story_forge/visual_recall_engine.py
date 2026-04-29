from __future__ import annotations

from typing import Any

from story_forge.models import Event, ImagePrompt, Scene, StoryRequest, StoryState
from story_forge.visual_artifact_schema import (
    ImageArtifactRecord,
    PendingVisualContext,
    VisualRecallResult,
    VisualSceneContext,
    apply_hook_updates,
    merge_unique,
    normalize_token,
    unique_strings,
    unique_tokens,
)
from story_forge.visual_memory_store import VisualMemoryStore


VISUAL_MATCH_PRIORITY = (
    ("character", 4),
    ("symbol", 3),
    ("location", 2),
    ("narrative arc", 1),
)

VISUAL_METADATA_KEYS = {
    "cartridge_id",
    "scene_id",
    "event_type",
    "character_ids",
    "location",
    "symbols",
    "visual_tags",
    "continuity_hooks",
    "tone_profile",
    "major",
    "narrative_arc",
    "force_image_event",
    "image_path",
    "source_image_path",
    "continuity_hook_updates",
}


class VisualRecallEngine:
    def __init__(self, store: VisualMemoryStore) -> None:
        self.store = store

    def build_scene_context(
        self,
        state: StoryState,
        request: StoryRequest,
        scene: Scene,
        events: list[Event],
    ) -> VisualSceneContext:
        event = events[-1] if events else None
        visual_metadata = self._visual_metadata(request.metadata)
        character_ids = self._extract_character_ids(visual_metadata, event)
        symbols = self._extract_symbols(visual_metadata, event)
        tone_profile = (
            str(visual_metadata.get("tone_profile") or "").strip()
            or scene.tone
        )
        return VisualSceneContext(
            cartridge_id=str(
                visual_metadata.get("cartridge_id")
                or state.world_pack_id
                or "default"
            ),
            scene_id=str(visual_metadata.get("scene_id") or f"scene_{state.turn_count + 1:04d}"),
            event_type=str(visual_metadata.get("event_type") or getattr(event, "event_type", "scene")),
            character_ids=character_ids,
            location=str(
                visual_metadata.get("location")
                or getattr(event, "next_location_id", None)
                or getattr(event, "location_id", None)
                or state.player_state.current_location_id
                or "unplaced"
            ),
            symbols=symbols,
            visual_tags=self._extract_visual_tags(visual_metadata, scene),
            continuity_hooks=self._string_list(visual_metadata.get("continuity_hooks")),
            tone_profile=tone_profile,
            narrative_arc=str(
                visual_metadata.get("narrative_arc")
                or state.scenario_position.current_arc
                or "default"
            ),
            major=self._is_major(visual_metadata, event),
            force_image_event=self._bool_value(visual_metadata.get("force_image_event")),
            source_image_path=str(
                visual_metadata.get("image_path")
                or visual_metadata.get("source_image_path")
                or ""
            ),
            continuity_hook_updates=self._hook_updates(visual_metadata.get("continuity_hook_updates")),
        )

    def recall(
        self,
        state: StoryState,
        scene_context: VisualSceneContext,
    ) -> VisualRecallResult:
        candidate_ids: set[str] = set()
        for character_id in scene_context.character_ids:
            candidate_ids.update(
                artifact.artifact_id for artifact in self.store.find_by_character(character_id)
            )
        if scene_context.location:
            candidate_ids.update(
                artifact.artifact_id for artifact in self.store.find_by_location(scene_context.location)
            )
        for symbol in scene_context.symbols:
            candidate_ids.update(
                artifact.artifact_id for artifact in self.store.find_by_symbol(symbol)
            )
        if scene_context.narrative_arc:
            candidate_ids.update(
                artifact.artifact_id for artifact in self.store.find_by_arc(scene_context.narrative_arc)
            )

        scored: list[tuple[int, str, ImageArtifactRecord, list[str]]] = []
        for artifact_id in candidate_ids:
            artifact = self.store.get_artifact(artifact_id)
            if artifact is None:
                continue
            if not (artifact.major or artifact.continuity_hooks):
                continue
            reasons = self._match_reasons(scene_context, artifact)
            if not reasons:
                continue
            score = self._score_reasons(reasons)
            scored.append((score, artifact.timestamp, artifact, reasons))

        scored.sort(key=lambda item: (item[0], item[1], item[2].artifact_id), reverse=True)
        artifacts = [item[2] for item in scored[:3]]
        if not artifacts:
            pending = state.visual_memory.pending_context
            if pending is not None and pending.narrative_arc and pending.narrative_arc != scene_context.narrative_arc:
                state.visual_memory.pending_context = None
            return VisualRecallResult(triggered=False)

        reasons: list[str] = []
        hooks: list[str] = []
        symbols: list[str] = []
        for _, _, artifact, artifact_reasons in scored[:3]:
            for reason in artifact_reasons:
                if reason not in reasons:
                    reasons.append(reason)
            hooks = merge_unique(hooks, artifact.continuity_hooks)
            symbols = merge_unique(symbols, artifact.symbols)

        result = VisualRecallResult(
            triggered=True,
            artifacts=artifacts,
            continuity_hooks=hooks,
            symbols=symbols,
            match_reasons=reasons,
            context=self._context_from_reasons(reasons),
        )
        state.visual_memory.last_recall_artifact_ids = result.artifact_ids
        return result

    def attach_recall_context(
        self,
        state: StoryState,
        image_prompt: ImagePrompt,
        scene_context: VisualSceneContext,
        recall_result: VisualRecallResult,
    ) -> ImagePrompt:
        pending = self._pending_for_scene(state, scene_context)
        recalled_hooks = merge_unique(
            pending.continuity_hooks if pending is not None else [],
            recall_result.continuity_hooks,
        )
        recalled_hooks = apply_hook_updates(recalled_hooks, scene_context.continuity_hook_updates)
        image_prompt.continuity_hooks = unique_tokens(
            merge_unique(recalled_hooks, scene_context.continuity_hooks)
        )
        image_prompt.symbols = unique_tokens(
            merge_unique(scene_context.symbols, recall_result.symbols, pending.symbols if pending else [])
        )
        image_prompt.recall_artifact_ids = unique_strings(
            merge_unique(recall_result.artifact_ids, pending.artifact_ids if pending else [])
        )
        image_prompt.recall_context = recall_result.context or (pending.context if pending is not None else "")
        image_prompt.tone_profile = scene_context.tone_profile or image_prompt.mood
        return image_prompt

    def store_pending_context(
        self,
        state: StoryState,
        scene_context: VisualSceneContext,
        recall_result: VisualRecallResult,
    ) -> None:
        pending = self._pending_for_scene(state, scene_context)
        if not recall_result.triggered and pending is None:
            return
        artifact_ids = unique_strings(
            merge_unique(
                recall_result.artifact_ids,
                pending.artifact_ids if pending is not None else [],
            )
        )
        hooks = unique_tokens(
            merge_unique(
                recall_result.continuity_hooks,
                pending.continuity_hooks if pending is not None else [],
            )
        )
        symbols = unique_tokens(
            merge_unique(
                recall_result.symbols,
                pending.symbols if pending is not None else [],
            )
        )
        reasons = unique_strings(
            merge_unique(
                recall_result.match_reasons,
                pending.match_reasons if pending is not None else [],
            )
        )
        context = recall_result.context or (pending.context if pending is not None else "")
        if not artifact_ids and not hooks and not symbols:
            return
        state.visual_memory.pending_context = PendingVisualContext(
            artifact_ids=artifact_ids,
            continuity_hooks=hooks,
            symbols=symbols,
            match_reasons=reasons,
            context=context or self._context_from_reasons(reasons),
            narrative_arc=scene_context.narrative_arc,
            location=scene_context.location,
            character_ids=scene_context.character_ids,
        )

    def store_artifact(
        self,
        state: StoryState,
        scene_context: VisualSceneContext,
        image_prompt: ImagePrompt,
    ) -> ImageArtifactRecord:
        artifact = ImageArtifactRecord(
            artifact_id="",
            cartridge_id=scene_context.cartridge_id,
            scene_id=scene_context.scene_id,
            event_type=scene_context.event_type,
            character_ids=scene_context.character_ids,
            location=scene_context.location,
            symbols=image_prompt.symbols or scene_context.symbols,
            visual_tags=scene_context.visual_tags,
            continuity_hooks=image_prompt.continuity_hooks,
            tone_profile=image_prompt.tone_profile or scene_context.tone_profile,
            narrative_arc=scene_context.narrative_arc,
            major=scene_context.major or bool(image_prompt.continuity_hooks),
        )
        stored = self.store.store_artifact(
            artifact,
            source_image_path=scene_context.source_image_path or None,
        )
        image_prompt.artifact_id = stored.artifact_id
        if stored.artifact_id not in state.visual_memory.artifact_ids:
            state.visual_memory.artifact_ids.append(stored.artifact_id)
        for hook in stored.continuity_hooks:
            state.visual_memory.hook_state[hook] = stored.artifact_id
        state.visual_memory.pending_context = None
        return stored

    def recall_summary(self, result: VisualRecallResult) -> dict[str, object]:
        return {
            "triggered": result.triggered,
            "artifact_ids": result.artifact_ids,
            "hooks": list(result.continuity_hooks),
            "symbols": list(result.symbols),
            "match_reasons": list(result.match_reasons),
            "context": result.context,
        }

    def artifact_summary(self, artifact: ImageArtifactRecord | None) -> dict[str, object]:
        if artifact is None:
            return {"stored": False}
        return {
            "stored": True,
            "artifact_id": artifact.artifact_id,
            "image_path": artifact.image_path,
            "metadata_path": artifact.metadata_path,
            "cartridge_id": artifact.cartridge_id,
            "scene_id": artifact.scene_id,
        }

    def artifact_error_summary(self, message: str) -> dict[str, object]:
        return {
            "stored": False,
            "error": str(message or "").strip(),
        }

    def memory_summary(self, state: StoryState) -> dict[str, object]:
        pending = state.visual_memory.pending_context
        return {
            "artifact_count": len(state.visual_memory.artifact_ids),
            "hook_count": len(state.visual_memory.hook_state),
            "pending_recall": pending is not None,
            "pending_hooks": list(pending.continuity_hooks) if pending is not None else [],
            "last_recall_artifact_ids": list(state.visual_memory.last_recall_artifact_ids),
        }

    def _match_reasons(
        self,
        scene_context: VisualSceneContext,
        artifact: ImageArtifactRecord,
    ) -> list[str]:
        reasons: list[str] = []
        if set(scene_context.character_ids) & set(artifact.character_ids):
            reasons.append("character")
        if scene_context.location and artifact.location == scene_context.location:
            reasons.append("location")
        if set(scene_context.symbols) & set(artifact.symbols):
            reasons.append("symbol")
        if scene_context.narrative_arc and artifact.narrative_arc == scene_context.narrative_arc:
            reasons.append("narrative arc")
        return reasons

    def _score_reasons(self, reasons: list[str]) -> int:
        score = 0
        for reason, weight in VISUAL_MATCH_PRIORITY:
            if reason in reasons:
                score += weight
        return score

    def _context_from_reasons(self, reasons: list[str]) -> str:
        ordered = [reason for reason, _ in VISUAL_MATCH_PRIORITY if reason in reasons]
        return " + ".join(ordered) + " match" if ordered else ""

    def _pending_for_scene(
        self,
        state: StoryState,
        scene_context: VisualSceneContext,
    ) -> PendingVisualContext | None:
        pending = state.visual_memory.pending_context
        if pending is None:
            return None
        if pending.narrative_arc and pending.narrative_arc != scene_context.narrative_arc:
            return None
        return pending

    def _visual_metadata(self, metadata: dict[str, Any] | None) -> dict[str, Any]:
        base = dict(metadata or {})
        visual = {}
        nested = base.get("visual")
        if isinstance(nested, dict):
            visual.update(nested)
        for key in VISUAL_METADATA_KEYS:
            if key in base and key not in visual:
                visual[key] = base[key]
        return visual

    def _extract_character_ids(
        self,
        metadata: dict[str, Any],
        event: Event | None,
    ) -> list[str]:
        explicit = self._string_list(metadata.get("character_ids"))
        if explicit:
            return explicit
        if event is None:
            return []
        return [participant for participant in event.participants if participant != "player"]

    def _extract_symbols(
        self,
        metadata: dict[str, Any],
        event: Event | None,
    ) -> list[str]:
        explicit = self._string_list(metadata.get("symbols"))
        if explicit:
            return explicit
        if event is None:
            return []
        return [
            normalize_token(tag)
            for tag in event.tags
            if tag and not str(tag).startswith("template:")
        ]

    def _extract_visual_tags(
        self,
        metadata: dict[str, Any],
        scene: Scene,
    ) -> list[str]:
        explicit = self._string_list(metadata.get("visual_tags"))
        if explicit:
            return explicit
        return unique_tokens([scene.tone, *scene.consequence_tags])

    def _is_major(
        self,
        metadata: dict[str, Any],
        event: Event | None,
    ) -> bool:
        if "major" in metadata:
            return self._bool_value(metadata.get("major"))
        return bool(event is not None and event.impact_level >= 4)

    def _bool_value(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    def _string_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return unique_tokens([part for part in value.split(",")])
        if isinstance(value, (list, tuple, set)):
            return unique_tokens([str(item) for item in value])
        return []

    def _hook_updates(self, value: Any) -> dict[str, str]:
        if isinstance(value, dict):
            return {
                normalize_token(source): normalize_token(target)
                for source, target in value.items()
                if normalize_token(source) and normalize_token(target)
            }
        if isinstance(value, list):
            updates: dict[str, str] = {}
            for item in value:
                if not isinstance(item, dict):
                    continue
                source = normalize_token(item.get("from", ""))
                target = normalize_token(item.get("to", ""))
                if source and target:
                    updates[source] = target
            return updates
        return {}
