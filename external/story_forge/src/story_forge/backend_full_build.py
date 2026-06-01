from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Callable
import uuid

from story_forge.app_paths import ensure_private_directory, user_data_root
from story_forge.contracts.engine_handoff import EngineHandoffInput


def _now_iso() -> str:
    return datetime.now().isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


_DIALOGUE_SKIP_PREFIXES = ("SHOT", "FADE", "INT.", "EXT.", "CUT TO")


@dataclass(slots=True)
class Entity:
    id: str = field(default_factory=lambda: _new_id("entity"))
    name: str = ""
    role: str = ""
    description: str = ""
    emotional_state: str = "neutral"


@dataclass(slots=True)
class Relationship:
    entity1_id: str
    entity2_id: str
    type: str
    intensity: float = 0.0


@dataclass(slots=True)
class NarrativeState:
    prompt: str
    characters: list[dict[str, Any]] = field(default_factory=list)
    setting: str = ""
    tone: str = "dark_fantasy"
    key_moments: list[str] = field(default_factory=list)
    beat_summaries: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SceneObject:
    scene_id: str
    narrative_state: NarrativeState
    entities: list[Entity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    timestamp: str = field(default_factory=_now_iso)


@dataclass(slots=True, frozen=True)
class FrozenSceneObject:
    scene_id: str
    narrative_state: NarrativeState
    entities: tuple[Entity, ...] = field(default_factory=tuple)
    relationships: tuple[Relationship, ...] = field(default_factory=tuple)
    timestamp: str = field(default_factory=_now_iso)


@dataclass(slots=True)
class Shot:
    shot_number: int
    description: str
    framing: str
    visual_intent: str = ""
    subject: str = ""
    action: str = ""
    intent: str = ""


@dataclass(slots=True)
class ShotList:
    scene_id: str
    shots: list[Shot] = field(default_factory=list)
    total_duration_estimate: float = 0.0


@dataclass(slots=True)
class CinematicShot:
    shot_number: int
    description: str
    framing: str
    visual_intent: str
    subject: str = ""
    action: str = ""
    intent: str = ""
    camera_motion: str = ""


@dataclass(slots=True)
class CinematicShotList:
    scene_id: str
    shots: list[CinematicShot] = field(default_factory=list)


@dataclass(slots=True)
class TemporalShot:
    shot_number: int
    description: str
    framing: str
    visual_intent: str
    subject: str = ""
    action: str = ""
    intent: str = ""
    camera_motion: str = ""
    duration_seconds: float = 0.0
    pacing: str = "medium"


@dataclass(slots=True)
class TemporalShotList:
    scene_id: str
    shots: list[TemporalShot] = field(default_factory=list)


@dataclass(slots=True)
class ContinuityReport:
    scene_id: str
    shots: list[TemporalShot] = field(default_factory=list)
    passed: bool = False
    issues: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FinalSequence:
    scene_id: str
    shots: list[TemporalShot] = field(default_factory=list)
    locked_sequence: list[dict[str, Any]] = field(default_factory=list)
    resolution_log: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AuditEntry:
    stage: int
    name: str
    status: str
    timestamp: str
    output_hash: str
    prev_hash: str | None = None
    notes: str | None = None


@dataclass(slots=True)
class ExportPackage:
    scene_id: str
    video_path: str | None
    screenplay: str
    shot_list_json: str
    metadata: dict[str, Any] = field(default_factory=dict)
    audit_log: list[AuditEntry] = field(default_factory=list)


@dataclass(slots=True)
class BackendBuildArtifact:
    build_id: str
    session_id: str
    output_dir: str
    narrative_state: NarrativeState
    scene_object: SceneObject
    frozen_scene_object: FrozenSceneObject
    shot_list: ShotList
    cinematic_shot_list: CinematicShotList
    temporal_shot_list: TemporalShotList
    continuity_report: ContinuityReport
    final_sequence: FinalSequence
    export_package: ExportPackage
    screenplay_path: str
    shot_list_path: str
    metadata_path: str
    audit_path: str
    audit_witness: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "build_id": self.build_id,
            "session_id": self.session_id,
            "output_dir": self.output_dir,
            "screenplay_path": self.screenplay_path,
            "shot_list_path": self.shot_list_path,
            "metadata_path": self.metadata_path,
            "audit_path": self.audit_path,
            "scene_id": self.export_package.scene_id,
            "video_path": self.export_package.video_path,
            "scene_count": len(self.shot_list.shots),
            "continuity_passed": self.continuity_report.passed,
            "continuity_issues": list(self.continuity_report.issues),
            "resolution_log": list(self.final_sequence.resolution_log),
            "audit_entries": len(self.export_package.audit_log),
            "audit_witness": self.audit_witness,
            "metadata": deepcopy(self.export_package.metadata),
        }


def _validate_characters(characters: list[dict[str, Any]]) -> None:
    names = [str(entry.get("name", "")).strip() for entry in characters if str(entry.get("name", "")).strip()]
    duplicates = {name for name in names if names.count(name) > 1}
    if duplicates:
        raise ValueError(f"Duplicate character names not allowed: {sorted(duplicates)}")


def _scrub_ids_and_timestamps(data: Any) -> Any:
    if is_dataclass(data):
        return _scrub_ids_and_timestamps(asdict(data))
    if isinstance(data, dict):
        return {
            key: _scrub_ids_and_timestamps(value)
            for key, value in data.items()
            if key not in {"id", "timestamp"}
        }
    if isinstance(data, list):
        return [_scrub_ids_and_timestamps(item) for item in data]
    if isinstance(data, tuple):
        return [_scrub_ids_and_timestamps(item) for item in data]
    return data


def _normalize_character_name(value: str) -> str:
    cleaned = " ".join(str(value or "").replace("_", " ").split())
    return cleaned.title()


def _iter_dialogue_pairs(text: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if ":" not in line:
            continue
        speaker_text, spoken_text = line.split(":", 1)
        speaker = speaker_text.strip()
        spoken = spoken_text.strip()
        if not speaker or not spoken:
            continue
        if any(speaker.upper().startswith(prefix) for prefix in _DIALOGUE_SKIP_PREFIXES):
            continue
        rows.append((speaker, spoken))
    return rows


def _infer_characters_from_presented_text(text: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for speaker, _ in _iter_dialogue_pairs(text):
        character_name = _normalize_character_name(speaker)
        key = character_name.upper()
        if not character_name or key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "name": character_name,
                "role": "participant",
                "description": f"Speaker inferred from presented output: {character_name}",
                "emotional_state": "neutral",
            }
        )
    return rows


def _cue_timeline(shots: list["TemporalShot"]) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    cursor = 0.0
    for index, shot in enumerate(shots, start=1):
        duration = float(shot.duration_seconds or 0.0)
        timeline.append(
            {
                "shot_number": int(shot.shot_number or index),
                "cue_start_seconds": cursor,
                "duration_seconds": duration,
            }
        )
        cursor += duration
    return timeline


def _estimate_text_duration(text: str) -> float:
    words = len(str(text or "").split())
    return max(0.6, words / 2.4)


def build_audio_line_metadata(
    handoff: EngineHandoffInput,
    scene_object: "SceneObject",
    temporal_shot_list: "TemporalShotList",
) -> dict[str, Any]:
    timeline = _cue_timeline(list(temporal_shot_list.shots))
    entities_by_name = {
        entity.name.upper(): entity
        for entity in scene_object.entities
        if str(entity.name or "").strip()
    }

    dialogue_lines: list[dict[str, Any]] = []
    for index, (speaker, spoken_text) in enumerate(_iter_dialogue_pairs(handoff.presented_output.text)):
        cue = timeline[min(index, len(timeline) - 1)] if timeline else {
            "shot_number": index + 1,
            "cue_start_seconds": 0.0,
            "duration_seconds": 0.0,
        }
        character_name = _normalize_character_name(speaker)
        entity = entities_by_name.get(character_name.upper())
        dialogue_lines.append(
            {
                "shot_number": int(cue["shot_number"]),
                "character_id": entity.id if entity is not None else "",
                "character_name": character_name,
                "role": entity.role if entity is not None else "participant",
                "text": spoken_text,
                "cue_start_seconds": float(cue["cue_start_seconds"]),
                "estimated_duration_seconds": _estimate_text_duration(spoken_text),
            }
        )

    staged_units = list(handoff.staged_plan.staged_units)
    narration_lines: list[dict[str, Any]] = []
    for index, cue in enumerate(timeline):
        shot = temporal_shot_list.shots[index]
        summary = ""
        if index < len(staged_units):
            summary = str(staged_units[index].summary or "").strip()
        text = summary or str(shot.description or "").strip()
        if not text:
            continue
        narration_lines.append(
            {
                "shot_number": int(cue["shot_number"]),
                "text": text,
                "cue_start_seconds": float(cue["cue_start_seconds"]),
                "estimated_duration_seconds": _estimate_text_duration(text),
                "is_explicit": True,
            }
        )

    return {
        "dialogue_lines": dialogue_lines,
        "narration_lines": narration_lines,
        "presented_output_text": handoff.presented_output.text,
    }


def hash_model(model: Any, prev_hash: str | None) -> str:
    payload = {
        "data": _scrub_ids_and_timestamps(model),
        "prev_hash": prev_hash,
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def hash_audit_log(entries: list[AuditEntry]) -> str:
    payload = [_scrub_ids_and_timestamps(entry) for entry in entries]
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class PipelineStage(ABC):
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        raise NotImplementedError


def enforce_types(input_type: type, output_type: type):
    def decorator(fn):
        def wrapper(self, input_data):
            if not isinstance(input_data, input_type):
                raise TypeError(
                    f"{self.__class__.__name__} expected {input_type.__name__}, "
                    f"got {type(input_data).__name__}"
                )
            result = fn(self, input_data)
            if not isinstance(result, output_type):
                raise TypeError(
                    f"{self.__class__.__name__} returned {type(result).__name__}, "
                    f"expected {output_type.__name__}"
                )
            return result

        return wrapper

    return decorator


class SceneIntake(PipelineStage):
    @enforce_types(NarrativeState, SceneObject)
    def process(self, input_data: NarrativeState) -> SceneObject:
        _validate_characters(input_data.characters)
        entities = [
            Entity(
                name=str(character.get("name", "")).strip(),
                role=str(character.get("role", "participant") or "participant"),
                description=str(character.get("description", "")).strip(),
                emotional_state=str(character.get("emotional_state", "neutral") or "neutral"),
            )
            for character in input_data.characters
            if str(character.get("name", "")).strip()
        ]
        return SceneObject(
            scene_id=_new_id("scene"),
            narrative_state=deepcopy(input_data),
            entities=entities,
            relationships=[],
        )


class NarrativeLock(PipelineStage):
    @enforce_types(SceneObject, FrozenSceneObject)
    def process(self, input_data: SceneObject) -> FrozenSceneObject:
        return FrozenSceneObject(
            scene_id=input_data.scene_id,
            narrative_state=deepcopy(input_data.narrative_state),
            entities=tuple(deepcopy(input_data.entities)),
            relationships=tuple(deepcopy(input_data.relationships)),
            timestamp=input_data.timestamp,
        )


class PreVisualization(PipelineStage):
    @enforce_types(FrozenSceneObject, ShotList)
    def process(self, input_data: FrozenSceneObject) -> ShotList:
        key_moments = list(input_data.narrative_state.key_moments)
        beat_summaries = list(input_data.narrative_state.beat_summaries)
        if not key_moments:
            key_moments = ["Opening", "Confrontation", "Outcome"]
        subject = input_data.entities[0].name if input_data.entities else "Narrative Focus"
        shots: list[Shot] = []
        for index, moment in enumerate(key_moments, start=1):
            beat_summary = (
                beat_summaries[index - 1].strip()
                if index - 1 < len(beat_summaries) and beat_summaries[index - 1].strip()
                else input_data.narrative_state.setting
            )
            shots.append(
                Shot(
                    shot_number=index,
                    description=beat_summary or f"{moment} in {input_data.narrative_state.setting}",
                    framing="medium",
                    visual_intent="",
                    subject=subject,
                    action=moment,
                    intent="advance central dilemma",
                )
            )
        return ShotList(
            scene_id=input_data.scene_id,
            shots=shots,
            total_duration_estimate=float(len(shots) * 3.0),
        )


class CinematicInterpretation(PipelineStage):
    @enforce_types(ShotList, CinematicShotList)
    def process(self, input_data: ShotList) -> CinematicShotList:
        motions = ["slow pan", "static", "push in", "tracking", "handheld"]
        palette = [
            "moody chiaroscuro lighting",
            "harsh backlight and silhouettes",
            "soft diffused glow",
            "cold desaturated palette",
            "high contrast, sharp shadows",
        ]
        shots: list[CinematicShot] = []
        for index, shot in enumerate(input_data.shots):
            shots.append(
                CinematicShot(
                    shot_number=shot.shot_number,
                    description=shot.description,
                    framing=shot.framing,
                    visual_intent=shot.visual_intent or palette[index % len(palette)],
                    subject=shot.subject,
                    action=shot.action,
                    intent=shot.intent,
                    camera_motion=motions[index % len(motions)],
                )
            )
        return CinematicShotList(scene_id=input_data.scene_id, shots=shots)


class TemporalBinding(PipelineStage):
    @enforce_types(CinematicShotList, TemporalShotList)
    def process(self, input_data: CinematicShotList) -> TemporalShotList:
        last_index = len(input_data.shots) - 1
        shots: list[TemporalShot] = []
        for index, shot in enumerate(input_data.shots):
            if index == 0 or index == last_index:
                duration = 4.0
                pacing = "slow"
            else:
                duration = 2.5
                pacing = "medium"
            shots.append(
                TemporalShot(
                    shot_number=shot.shot_number,
                    description=shot.description,
                    framing=shot.framing,
                    visual_intent=shot.visual_intent,
                    subject=shot.subject,
                    action=shot.action,
                    intent=shot.intent,
                    camera_motion=shot.camera_motion,
                    duration_seconds=duration,
                    pacing=pacing,
                )
            )
        return TemporalShotList(scene_id=input_data.scene_id, shots=shots)


class ContinuityEnforcement(PipelineStage):
    @enforce_types(TemporalShotList, ContinuityReport)
    def process(self, input_data: TemporalShotList) -> ContinuityReport:
        issues: list[str] = []
        expected = 1
        for shot in input_data.shots:
            if shot.shot_number != expected:
                issues.append(
                    f"Shot numbering discontinuity at shot {shot.shot_number}, expected {expected}"
                )
                break
            expected += 1
            if shot.duration_seconds <= 0:
                issues.append(f"Shot {shot.shot_number} has non-positive duration.")
        intents = [shot.intent for shot in input_data.shots if shot.intent]
        if intents and len(set(intents)) > max(1, len(intents) // 2):
            issues.append("Intent changes too frequently across shots.")
        return ContinuityReport(
            scene_id=input_data.scene_id,
            shots=list(input_data.shots),
            passed=not issues,
            issues=issues,
        )


class AssemblyDirector(PipelineStage):
    @enforce_types(ContinuityReport, FinalSequence)
    def process(self, input_data: ContinuityReport) -> FinalSequence:
        resolution_log: list[str] = []
        if input_data.passed:
            resolution_log.append("All continuity checks passed - sequence locked.")
        else:
            resolution_log.append("Continuity issues detected; sequence locked with warnings.")
            resolution_log.extend(f"- {issue}" for issue in input_data.issues)
        locked_sequence = [
            {
                "shot_number": shot.shot_number,
                "description": shot.description,
                "framing": shot.framing,
                "camera_motion": shot.camera_motion,
                "visual_intent": shot.visual_intent,
                "duration_seconds": shot.duration_seconds,
                "pacing": shot.pacing,
                "subject": shot.subject,
                "action": shot.action,
                "intent": shot.intent,
            }
            for shot in input_data.shots
        ]
        return FinalSequence(
            scene_id=input_data.scene_id,
            shots=list(input_data.shots),
            locked_sequence=locked_sequence,
            resolution_log=resolution_log,
        )


class PackagingExport(PipelineStage):
    @enforce_types(FinalSequence, ExportPackage)
    def process(self, input_data: FinalSequence) -> ExportPackage:
        screenplay_lines = ["FADE IN:"]
        for shot in input_data.shots:
            screenplay_lines.append(
                f"SHOT {shot.shot_number} - {shot.description} ({shot.framing})"
            )
        shot_list_json = json.dumps(
            [_scrub_ids_and_timestamps(shot) for shot in input_data.shots],
            indent=2,
            sort_keys=True,
        )
        return ExportPackage(
            scene_id=input_data.scene_id,
            video_path=None,
            screenplay="\n".join(screenplay_lines),
            shot_list_json=shot_list_json,
            metadata={
                "generated_at": _now_iso(),
                "total_shots": len(input_data.shots),
                "resolution_log": list(input_data.resolution_log),
            },
            audit_log=[],
        )


def build_narrative_state_from_handoff(handoff: EngineHandoffInput) -> NarrativeState:
    staged_units = list(handoff.staged_plan.staged_units)
    first_summary = staged_units[0].summary if staged_units else handoff.scene_grammar.title
    tone = (
        ",".join(handoff.scene_grammar.emotional_tags[:2])
        if handoff.scene_grammar.emotional_tags
        else "dark_fantasy"
    )
    key_moments = [unit.title for unit in staged_units] or [handoff.scene_grammar.title]
    return NarrativeState(
        prompt=handoff.presented_output.text or handoff.scene_grammar.title,
        characters=_infer_characters_from_presented_text(handoff.presented_output.text),
        setting=first_summary,
        tone=tone,
        key_moments=key_moments,
        beat_summaries=[unit.summary for unit in staged_units],
    )


class StoryForgeBackendPipeline:
    def __init__(self, output_root: str | Path | None = None) -> None:
        if output_root is None:
            output_root = user_data_root() / "backend_builds"
        self.output_root = ensure_private_directory(output_root)
        self.stages: dict[int, PipelineStage] = {
            1: SceneIntake(),
            2: NarrativeLock(),
            3: PreVisualization(),
            4: CinematicInterpretation(),
            5: TemporalBinding(),
            6: ContinuityEnforcement(),
            7: AssemblyDirector(),
            8: PackagingExport(),
        }

    def run_from_handoff(
        self,
        *,
        session_id: str,
        handoff: EngineHandoffInput,
        source_mode: str,
        source_path: str,
        source_title: str,
    ) -> BackendBuildArtifact:
        narrative_state = build_narrative_state_from_handoff(handoff)
        return self.run(
            session_id=session_id,
            narrative_state=narrative_state,
            target=handoff.directional_context.target,
            source_mode=source_mode,
            source_path=source_path,
            source_title=source_title,
            supplemental_metadata_builder=lambda scene_object, temporal_shot_list: build_audio_line_metadata(
                handoff,
                scene_object,
                temporal_shot_list,
            ),
        )

    def run_movie_audio_pipeline(
        self,
        artifact: BackendBuildArtifact,
        **kwargs: Any,
    ) -> Any:
        from story_forge.movie_audio_pipeline import run_story_forge_movie_audio_pipeline

        return run_story_forge_movie_audio_pipeline(artifact, **kwargs)

    def run(
        self,
        *,
        session_id: str,
        narrative_state: NarrativeState,
        target: str,
        source_mode: str,
        source_path: str,
        source_title: str,
        supplemental_metadata_builder: Callable[[SceneObject, TemporalShotList], dict[str, Any]] | None = None,
    ) -> BackendBuildArtifact:
        audit_log: list[AuditEntry] = []
        prev_hash: str | None = None

        scene_object = self.stages[1].process(narrative_state)
        prev_hash = self._append_audit(audit_log, 1, self.stages[1], scene_object, prev_hash, "Scene intake complete.")

        frozen_scene = self.stages[2].process(scene_object)
        prev_hash = self._append_audit(audit_log, 2, self.stages[2], frozen_scene, prev_hash, "Narrative lock complete.")

        shot_list = self.stages[3].process(frozen_scene)
        prev_hash = self._append_audit(audit_log, 3, self.stages[3], shot_list, prev_hash, "Previsualization complete.")

        cinematic_shots = self.stages[4].process(shot_list)
        prev_hash = self._append_audit(audit_log, 4, self.stages[4], cinematic_shots, prev_hash, "Cinematic interpretation complete.")

        temporal_shots = self.stages[5].process(cinematic_shots)
        prev_hash = self._append_audit(audit_log, 5, self.stages[5], temporal_shots, prev_hash, "Temporal binding complete.")

        continuity = self.stages[6].process(temporal_shots)
        continuity_status = "Continuity verification passed." if continuity.passed else "Continuity verification locked with warnings."
        prev_hash = self._append_audit(audit_log, 6, self.stages[6], continuity, prev_hash, continuity_status)

        final_sequence = self.stages[7].process(continuity)
        prev_hash = self._append_audit(audit_log, 7, self.stages[7], final_sequence, prev_hash, "Assembly director locked sequence.")

        export_package = self.stages[8].process(final_sequence)
        export_package.audit_log = list(audit_log)
        export_package.metadata.update(
            {
                "source_title": source_title,
                "source_mode": source_mode,
                "source_path": source_path,
                "target": target,
                "tone": narrative_state.tone,
                "scene_id": final_sequence.scene_id,
                "audit_digest": hash_audit_log(audit_log),
                "continuity_passed": continuity.passed,
                "continuity_issues": list(continuity.issues),
            }
        )
        if supplemental_metadata_builder is not None:
            export_package.metadata.update(
                deepcopy(supplemental_metadata_builder(scene_object, temporal_shots))
            )
        prev_hash = self._append_audit(audit_log, 8, self.stages[8], export_package, prev_hash, "Packaging export complete.")
        export_package.audit_log = list(audit_log)
        export_package.metadata["audit_digest"] = hash_audit_log(audit_log)

        build_id = _new_id("backend_build")
        output_dir = ensure_private_directory(self.output_root / session_id / build_id)
        screenplay_path = output_dir / "screenplay.txt"
        shot_list_path = output_dir / "shot_list.json"
        metadata_path = output_dir / "metadata.json"
        audit_path = output_dir / "audit_log.json"

        screenplay_path.write_text(export_package.screenplay, encoding="utf-8")
        shot_list_path.write_text(export_package.shot_list_json, encoding="utf-8")
        metadata_path.write_text(json.dumps(export_package.metadata, indent=2, sort_keys=True), encoding="utf-8")
        audit_path.write_text(
            json.dumps([_scrub_ids_and_timestamps(entry) for entry in audit_log], indent=2, sort_keys=True),
            encoding="utf-8",
        )

        return BackendBuildArtifact(
            build_id=build_id,
            session_id=session_id,
            output_dir=str(output_dir),
            narrative_state=narrative_state,
            scene_object=scene_object,
            frozen_scene_object=frozen_scene,
            shot_list=shot_list,
            cinematic_shot_list=cinematic_shots,
            temporal_shot_list=temporal_shots,
            continuity_report=continuity,
            final_sequence=final_sequence,
            export_package=export_package,
            screenplay_path=str(screenplay_path),
            shot_list_path=str(shot_list_path),
            metadata_path=str(metadata_path),
            audit_path=str(audit_path),
            audit_witness=export_package.metadata["audit_digest"],
        )

    def _append_audit(
        self,
        audit_log: list[AuditEntry],
        stage_number: int,
        stage: PipelineStage,
        stage_output: Any,
        prev_hash: str | None,
        notes: str,
    ) -> str:
        output_hash = hash_model(stage_output, prev_hash)
        audit_log.append(
            AuditEntry(
                stage=stage_number,
                name=stage.__class__.__name__,
                status="passed",
                timestamp=_now_iso(),
                output_hash=output_hash,
                prev_hash=prev_hash,
                notes=notes,
            )
        )
        return output_hash
