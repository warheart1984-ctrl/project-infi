from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
from importlib import import_module
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

from story_forge.backend_full_build import BackendBuildArtifact, TemporalShot
from story_forge.render_manager import (
    LocalCinematicAdapter,
    ProviderAdapter,
    RenderIntent,
    RenderManager,
    RenderResult,
    StoryboardAdapter,
    intent_to_prompt,
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _style_hash(style: dict[str, Any]) -> str:
    raw = json.dumps(style, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _stable_seed(*parts: str) -> int:
    raw = "|".join(parts)
    return int(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8], 16)


DEFAULT_RENDER_STYLE = {
    "lighting": "low-key cinematic",
    "palette": "cold_blue_amber",
    "lens": "35mm",
    "grain": "subtle",
    "contrast": "soft_crush",
    "atmosphere": "clean_air",
    "texture": "weathered_stone",
    "composition": "centered_tension",
    "depth": "layered_midground",
    "practicals": "sparse_practicals",
    "blocking": "single_subject_center",
    "movement_energy": "restrained",
    "frame_signature": "soft_halo",
}
DEFAULT_STYLE_VERSION = "v1.2.0"


@dataclass(slots=True)
class VisualBeat:
    beat_id: str
    order_index: int
    shot_number: int
    heading: str
    summary: str
    image_prompt: str
    video_prompt: str
    clip_duration_seconds: int
    framing: str
    camera_motion: str
    render_intent: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VisualRenderPlan:
    title: str
    mode: str
    source_build_id: str
    source_scene_id: str
    tone: str
    beats: list[VisualBeat] = field(default_factory=list)
    created_at: str = field(default_factory=_utc_timestamp)


@dataclass(slots=True)
class VisualRenderResult:
    title: str
    mode: str
    output_dir: str
    manifest_path: str
    trailer_path: str
    clip_paths: list[str] = field(default_factory=list)
    image_paths: list[str] = field(default_factory=list)
    beat_count: int = 0
    render_mode: str = "auto"
    selected_adapters: list[str] = field(default_factory=list)
    assembler: str = "opencv"


@dataclass(slots=True, frozen=True)
class _VideoRuntimeModules:
    cv2: Any


class VisualGenerationBackendError(RuntimeError):
    pass


class RenderIntentBuilder:
    def build_for_plan(self, plan: VisualRenderPlan) -> list[RenderIntent]:
        intents: list[RenderIntent] = []
        for beat in plan.beats:
            payload = dict(beat.render_intent)
            try:
                intents.append(RenderIntent(**payload))
            except TypeError as exc:
                raise VisualGenerationBackendError(
                    f"Visual beat '{beat.beat_id}' did not contain a complete render intent."
                ) from exc
        return intents


class StoryForgeVisualBackend:
    def __init__(
        self,
        *,
        image_adapter=None,
        video_adapter=None,
        render_manager: RenderManager | None = None,
        render_mode: str = "auto",
        style: dict[str, Any] | None = None,
        style_version: str = DEFAULT_STYLE_VERSION,
        local_resolution: tuple[int, int] = (640, 360),
        local_fps: float = 12.0,
        provider_resolution: tuple[int, int] = (1280, 720),
    ) -> None:
        self.style = dict(style or DEFAULT_RENDER_STYLE)
        self.style_version = str(style_version or DEFAULT_STYLE_VERSION)
        self.style_hash = _style_hash(self.style)
        self.local_resolution = tuple(local_resolution)
        self.local_fps = float(local_fps)
        self.provider_resolution = tuple(provider_resolution)
        self.render_mode = str(render_mode or "auto").strip().lower()
        self.intent_builder = RenderIntentBuilder()
        self._runtime_cache: _VideoRuntimeModules | None = None

        if render_manager is not None:
            self.render_manager = render_manager
            return

        provider_adapter = None
        if image_adapter is not None and video_adapter is not None:
            provider_adapter = ProviderAdapter(
                image_adapter=image_adapter,
                video_adapter=video_adapter,
                resolution=self.provider_resolution,
            )
        self.render_manager = RenderManager(
            mode=self.render_mode,
            local_adapter=LocalCinematicAdapter(
                resolution=self.local_resolution,
                fps=self.local_fps,
            ),
            provider_adapter=provider_adapter,
            storyboard_adapter=StoryboardAdapter(
                resolution=self.local_resolution,
                fps=self.local_fps,
            ),
        )

    def build_plan(
        self,
        artifact: BackendBuildArtifact,
        *,
        title: str | None = None,
        mode: str = "proof_trailer",
        beat_count: int | None = None,
    ) -> VisualRenderPlan:
        shots = list(artifact.temporal_shot_list.shots)
        if not shots:
            raise VisualGenerationBackendError("Backend build did not contain any temporal shots.")

        normalized_mode = str(mode or "proof_trailer").strip().lower()
        if normalized_mode not in {"proof_trailer", "full_movie"}:
            raise VisualGenerationBackendError(
                "Visual render mode must be 'proof_trailer' or 'full_movie'."
            )

        if normalized_mode == "proof_trailer":
            target_beats = beat_count if beat_count is not None else min(6, len(shots))
            selected_shots = self._sample_evenly(shots, max(1, min(target_beats, len(shots))))
            default_clip_duration = 5
        else:
            selected_shots = shots
            default_clip_duration = 0

        render_title = str(title or artifact.export_package.metadata.get("source_title") or artifact.build_id).strip()
        tone = str(artifact.narrative_state.tone or "cinematic").strip()
        beats = [
            self._build_beat(
                artifact,
                shot,
                order_index=index,
                clip_duration_seconds=default_clip_duration,
            )
            for index, shot in enumerate(selected_shots, start=1)
        ]
        return VisualRenderPlan(
            title=render_title,
            mode=normalized_mode,
            source_build_id=artifact.build_id,
            source_scene_id=artifact.export_package.scene_id,
            tone=tone,
            beats=beats,
        )

    def render_proof_trailer(
        self,
        artifact: BackendBuildArtifact,
        *,
        output_root: str | Path,
        title: str | None = None,
        beat_count: int | None = None,
        render_mode: str | None = None,
    ) -> VisualRenderResult:
        plan = self.build_plan(
            artifact,
            title=title,
            mode="proof_trailer",
            beat_count=beat_count,
        )
        return self.render_plan(plan, output_root=output_root, render_mode=render_mode)

    def render_full_movie(
        self,
        artifact: BackendBuildArtifact,
        *,
        output_root: str | Path,
        title: str | None = None,
        render_mode: str | None = None,
    ) -> VisualRenderResult:
        plan = self.build_plan(
            artifact,
            title=title,
            mode="full_movie",
        )
        return self.render_plan(plan, output_root=output_root, render_mode=render_mode)

    def render_plan(
        self,
        plan: VisualRenderPlan,
        *,
        output_root: str | Path,
        render_mode: str | None = None,
    ) -> VisualRenderResult:
        output_dir = Path(output_root)
        output_dir.mkdir(parents=True, exist_ok=True)

        intents = self.intent_builder.build_for_plan(plan)
        requested_render_mode = str(render_mode or self.render_mode or "auto").strip().lower()
        render_results = self.render_manager.render_intents(
            intents,
            output_root=output_dir,
            mode=requested_render_mode,
        )
        self._validate_render_results(intents, render_results)

        manifest_beats: list[dict[str, Any]] = []
        image_paths: list[str] = []
        clip_paths: list[str] = []
        selected_adapters: set[str] = set()

        for beat, intent in zip(plan.beats, intents, strict=True):
            result = render_results[intent.shot_id]
            clip_path = str(result.clip_path or "").strip()
            if clip_path:
                clip_paths.append(clip_path)

            seed_image_path = str(result.metadata.get("seed_image_path", "") or "").strip()
            if seed_image_path:
                image_paths.append(seed_image_path)

            adapter_name = str(result.metadata.get("adapter", "") or "").strip()
            if adapter_name:
                selected_adapters.add(adapter_name)

            manifest_beats.append(
                {
                    **asdict(beat),
                    "render_intent": asdict(intent),
                    "image_path": seed_image_path,
                    "clip_path": clip_path,
                    "render_result": {
                        "frames": list(result.frames),
                        "clip_path": result.clip_path,
                        "duration_seconds": result.duration_seconds,
                        "metadata": result.metadata,
                    },
                }
            )

        trailer_path = output_dir / f"{self._slug(plan.title)}_{plan.mode}.mp4"
        assembler = self._stitch_clips([Path(path) for path in clip_paths], trailer_path)
        trailer_duration = self._clip_duration_seconds(trailer_path)

        manifest_path = output_dir / f"{self._slug(plan.title)}_{plan.mode}_manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "title": plan.title,
                    "mode": plan.mode,
                    "render_mode": requested_render_mode,
                    "source_build_id": plan.source_build_id,
                    "source_scene_id": plan.source_scene_id,
                    "tone": plan.tone,
                    "created_at": plan.created_at,
                    "trailer_path": str(trailer_path),
                    "trailer_duration_seconds": trailer_duration,
                    "selected_adapters": sorted(selected_adapters),
                    "assembler": assembler,
                    "beats": manifest_beats,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        return VisualRenderResult(
            title=plan.title,
            mode=plan.mode,
            output_dir=str(output_dir),
            manifest_path=str(manifest_path),
            trailer_path=str(trailer_path),
            clip_paths=clip_paths,
            image_paths=image_paths,
            beat_count=len(plan.beats),
            render_mode=requested_render_mode,
            selected_adapters=sorted(selected_adapters),
            assembler=assembler,
        )

    def _build_beat(
        self,
        artifact: BackendBuildArtifact,
        shot: TemporalShot,
        *,
        order_index: int,
        clip_duration_seconds: int,
    ) -> VisualBeat:
        scene_id = str(artifact.export_package.scene_id or artifact.build_id).strip()
        title = str(artifact.export_package.metadata.get("source_title") or artifact.build_id).strip()
        base_setting = str(artifact.narrative_state.setting or title or "cinematic environment").strip()
        environment = self._derive_environment(base_setting, shot, title)
        environment_context = "|".join(
            [
                environment,
                str(shot.description or "").strip(),
                str(shot.visual_intent or "").strip(),
                str(shot.intent or "").strip(),
            ]
        )
        environment_id = hashlib.sha256(f"{scene_id}:{environment_context}".encode("utf-8")).hexdigest()[:16]

        subject = str(shot.subject or "the central figure").strip()
        action = str(shot.action or shot.description or "holds frame").strip()
        intent_text = str(shot.intent or artifact.narrative_state.tone or "cinematic").strip()
        visual_intent = str(shot.visual_intent or intent_text).strip()
        heading = str(shot.action or shot.description or f"Shot {shot.shot_number}").strip()
        summary = str(shot.description or shot.intent or heading).strip()
        pacing = str(shot.pacing or "medium").strip().lower()
        duration = float(clip_duration_seconds or max(1.0, round(float(shot.duration_seconds or 1.0))))
        shot_id = f"{scene_id}:{shot.shot_number}"
        shot_style = self._derive_shot_style(
            artifact,
            shot,
            order_index=order_index,
            total_shots=len(artifact.temporal_shot_list.shots),
            base_setting=base_setting,
        )
        shot_style_hash = _style_hash(shot_style)

        render_intent = RenderIntent(
            scene_id=scene_id,
            shot_id=shot_id,
            subject=subject,
            action=action,
            environment=environment,
            environment_id=environment_id,
            intent=intent_text,
            visual_intent=visual_intent,
            framing=str(shot.framing or "medium").strip(),
            camera_motion=str(shot.camera_motion or "slow cinematic drift").strip(),
            pacing=pacing,
            duration_seconds=duration,
            frame_count=self._frame_count(duration, pacing),
            motion_curve=self._motion_curve(pacing),
            lens_profile=str(shot_style.get("lens", self.style.get("lens", "35mm"))),
            color_profile=str(shot_style.get("palette", self.style.get("palette", "cold_blue_amber"))),
            grain_profile=str(shot_style.get("grain", self.style.get("grain", "subtle"))),
            seed=_stable_seed(scene_id, shot_id, subject, action, environment_id, shot_style_hash),
            style=shot_style,
            style_hash=shot_style_hash,
            style_version=self.style_version,
        )
        prompts = intent_to_prompt(render_intent)
        return VisualBeat(
            beat_id=f"beat_{order_index:03d}",
            order_index=order_index,
            shot_number=shot.shot_number,
            heading=heading,
            summary=summary,
            image_prompt=prompts.still_prompt,
            video_prompt=prompts.motion_prompt,
            clip_duration_seconds=int(duration),
            framing=render_intent.framing,
            camera_motion=render_intent.camera_motion,
            render_intent=asdict(render_intent),
        )

    def _frame_count(self, duration_seconds: float, pacing: str) -> int:
        base_fps = self.local_fps
        if pacing == "slow":
            effective_fps = max(base_fps, 14.0)
        elif pacing == "fast":
            effective_fps = max(8.0, base_fps - 2.0)
        else:
            effective_fps = base_fps
        return max(8, int(round(duration_seconds * effective_fps)))

    def _motion_curve(self, pacing: str) -> str:
        if pacing == "slow":
            return "ease_in_out"
        if pacing == "fast":
            return "linear"
        return "ease_out"

    def _derive_environment(self, base_setting: str, shot: TemporalShot, title: str) -> str:
        detail = self._clean_scene_phrase(str(shot.description or shot.action or shot.visual_intent or "").strip())
        fragments = [fragment for fragment in (base_setting, detail) if fragment]
        unique_fragments: list[str] = []
        seen: set[str] = set()
        for fragment in fragments:
            normalized = fragment.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            unique_fragments.append(fragment)
        environment = ", ".join(unique_fragments)
        return environment or title or "cinematic environment"

    def _derive_shot_style(
        self,
        artifact: BackendBuildArtifact,
        shot: TemporalShot,
        *,
        order_index: int,
        total_shots: int,
        base_setting: str,
    ) -> dict[str, Any]:
        framing = str(shot.framing or "medium").strip().lower()
        pacing = str(shot.pacing or "medium").strip().lower()
        camera_motion = str(shot.camera_motion or "").strip().lower()
        corpus = " ".join(
            [
                str(artifact.export_package.metadata.get("source_title", "") or ""),
                base_setting,
                str(shot.description or ""),
                str(shot.action or ""),
                str(shot.intent or ""),
                str(shot.visual_intent or ""),
            ]
        ).lower()
        progress = 0.0 if total_shots <= 1 else (max(0, shot.shot_number - 1) / max(1, total_shots - 1))
        side_variant = ("left", "center", "right")[shot.shot_number % 3]

        lens = self._select_lens_profile(framing=framing, pacing=pacing, camera_motion=camera_motion)
        palette = self._select_palette_profile(corpus=corpus, progress=progress)
        lighting = self._select_lighting_profile(corpus=corpus, progress=progress)
        grain = self._select_grain_profile(corpus=corpus, pacing=pacing)
        contrast = self._select_contrast_profile(corpus=corpus, lighting=lighting)
        atmosphere = self._select_atmosphere_profile(corpus=corpus)
        texture = self._select_texture_profile(corpus=corpus)
        practicals = self._select_practicals_profile(corpus=corpus, lighting=lighting)
        depth = self._select_depth_profile(framing=framing, atmosphere=atmosphere)
        composition = self._select_composition_profile(framing=framing, side_variant=side_variant, pacing=pacing)
        blocking = self._select_blocking_profile(framing=framing, corpus=corpus, side_variant=side_variant)
        movement_energy = self._select_movement_energy(pacing=pacing, camera_motion=camera_motion)
        frame_signature = self._select_frame_signature(corpus=corpus, atmosphere=atmosphere, practicals=practicals)

        style = dict(self.style)
        style.update(
            {
                "lighting": lighting,
                "palette": palette,
                "lens": lens,
                "grain": grain,
                "contrast": contrast,
                "atmosphere": atmosphere,
                "texture": texture,
                "composition": composition,
                "depth": depth,
                "practicals": practicals,
                "blocking": blocking,
                "movement_energy": movement_energy,
                "frame_signature": frame_signature,
                "shot_language": self._shot_language_descriptor(
                    composition=composition,
                    depth=depth,
                    lighting=lighting,
                    movement_energy=movement_energy,
                ),
                "order_index": order_index,
            }
        )
        return style

    def _clean_scene_phrase(self, value: str) -> str:
        if not value:
            return ""
        normalized = re.sub(r"\s+", " ", value).strip()
        first_clause = re.split(r"(?<=[.!?])\s+|;| -- | - ", normalized, maxsplit=1)[0].strip()
        words = first_clause.split()
        if len(words) > 14:
            first_clause = " ".join(words[:14]).strip() + "..."
        return first_clause

    def _contains_any(self, corpus: str, tokens: tuple[str, ...]) -> bool:
        return any(token in corpus for token in tokens)

    def _select_lens_profile(self, *, framing: str, pacing: str, camera_motion: str) -> str:
        if "close" in framing:
            return "75mm"
        if "wide" in framing:
            return "28mm" if pacing != "fast" else "24mm"
        if any(token in camera_motion for token in ("tracking", "handheld", "whip")):
            return "32mm"
        return "40mm"

    def _select_palette_profile(self, *, corpus: str, progress: float) -> str:
        if self._contains_any(corpus, ("blood", "fire", "ritual", "sacrifice", "burn")):
            return "ember_crimson_smoke"
        if self._contains_any(corpus, ("neon", "city", "street", "tower", "rain", "storm")):
            return "sodium_teal_noir"
        if self._contains_any(corpus, ("ocean", "water", "shore", "moon", "silver")):
            return "moon_silver_blue"
        if self._contains_any(corpus, ("forest", "garden", "moss", "green", "organic")):
            return "verdigris_gold_decay"
        if self._contains_any(corpus, ("archive", "cathedral", "stone", "dust", "bone", "hall")):
            return "bone_charcoal_amber"
        if progress > 0.72:
            return "ember_crimson_smoke"
        if progress < 0.28:
            return "moon_silver_blue"
        return "cold_blue_amber"

    def _select_lighting_profile(self, *, corpus: str, progress: float) -> str:
        if self._contains_any(corpus, ("neon", "city", "street", "station")):
            return "neon practical haze"
        if self._contains_any(corpus, ("ritual", "cathedral", "god", "altar", "temple")):
            return "ritual backlight and shafts"
        if self._contains_any(corpus, ("archive", "library", "hall", "room", "interior")):
            return "dusty motivated pools"
        if self._contains_any(corpus, ("ocean", "water", "moon", "shore")):
            return "silver horizon glow"
        if progress > 0.75:
            return "hard edge revelation"
        return "low-key cinematic"

    def _select_grain_profile(self, *, corpus: str, pacing: str) -> str:
        if self._contains_any(corpus, ("memory", "dream", "flashback", "grief", "ancient")):
            return "heavy"
        if pacing == "fast":
            return "clean"
        return "subtle"

    def _select_contrast_profile(self, *, corpus: str, lighting: str) -> str:
        if "neon" in lighting or self._contains_any(corpus, ("dread", "threat", "knife", "fear")):
            return "hard_crush"
        if self._contains_any(corpus, ("wonder", "longing", "beautiful", "radiant")):
            return "soft_bloom"
        return "soft_crush"

    def _select_atmosphere_profile(self, *, corpus: str) -> str:
        if self._contains_any(corpus, ("rain", "storm", "wet", "drizzle")):
            return "rain_mist"
        if self._contains_any(corpus, ("smoke", "fog", "mist", "haze")):
            return "smoke_haze"
        if self._contains_any(corpus, ("dust", "archive", "cathedral", "library")):
            return "dust_shafts"
        if self._contains_any(corpus, ("ocean", "shore", "water", "salt")):
            return "salt_air"
        return "clean_air"

    def _select_texture_profile(self, *, corpus: str) -> str:
        if self._contains_any(corpus, ("stone", "cathedral", "altar", "archive", "bone")):
            return "weathered_stone"
        if self._contains_any(corpus, ("metal", "machine", "steel", "factory", "industrial")):
            return "oxidized_metal"
        if self._contains_any(corpus, ("ocean", "water", "rain", "glass")):
            return "wet_glass"
        if self._contains_any(corpus, ("forest", "garden", "moss", "vine")):
            return "moss_patina"
        return "aged_film"

    def _select_practicals_profile(self, *, corpus: str, lighting: str) -> str:
        if "neon" in lighting:
            return "dense_neon_practicals"
        if self._contains_any(corpus, ("hall", "room", "archive", "interior", "candle")):
            return "motivated_warm_pools"
        if self._contains_any(corpus, ("ocean", "water", "shore", "rain")):
            return "horizon_glints"
        return "sparse_practicals"

    def _select_depth_profile(self, *, framing: str, atmosphere: str) -> str:
        if "close" in framing:
            return "shallow_subject_isolation"
        if "wide" in framing:
            return "deep_environment_layers"
        if atmosphere in {"rain_mist", "smoke_haze", "dust_shafts"}:
            return "occluded_depth_planes"
        return "layered_midground"

    def _select_composition_profile(self, *, framing: str, side_variant: str, pacing: str) -> str:
        if "wide" in framing:
            return f"negative_space_{side_variant}"
        if "close" in framing:
            return f"{side_variant}_weighted_portrait_pressure"
        if pacing == "fast":
            return f"{side_variant}_weighted_kinetic_frame"
        return f"{side_variant}_weighted_observation"

    def _select_blocking_profile(self, *, framing: str, corpus: str, side_variant: str) -> str:
        if self._contains_any(corpus, ("crowd", "chorus", "procession", "duel", "confront")):
            return f"multi_subject_{side_variant}"
        if "wide" in framing:
            return f"small_subject_{side_variant}"
        return f"single_subject_{side_variant}"

    def _select_movement_energy(self, *, pacing: str, camera_motion: str) -> str:
        if pacing == "fast" or any(token in camera_motion for token in ("tracking", "handheld", "whip")):
            return "restless"
        if pacing == "slow":
            return "ritual"
        return "measured"

    def _select_frame_signature(self, *, corpus: str, atmosphere: str, practicals: str) -> str:
        if atmosphere == "rain_mist":
            return "reflected_practicals"
        if practicals == "dense_neon_practicals":
            return "practical_bloom"
        if self._contains_any(corpus, ("silhouette", "shadow", "eclipse")):
            return "hard_silhouette"
        if self._contains_any(corpus, ("door", "arch", "threshold", "window")):
            return "framed_threshold"
        return "soft_halo"

    def _shot_language_descriptor(
        self,
        *,
        composition: str,
        depth: str,
        lighting: str,
        movement_energy: str,
    ) -> str:
        return f"{composition}, {depth}, {lighting}, {movement_energy}"

    def _sample_evenly(self, shots: list[TemporalShot], count: int) -> list[TemporalShot]:
        if count >= len(shots):
            return list(shots)
        indexes = {
            round(position * (len(shots) - 1) / max(1, count - 1))
            for position in range(count)
        }
        return [shots[index] for index in sorted(indexes)]

    def _validate_render_results(
        self,
        intents: list[RenderIntent],
        results: dict[str, RenderResult],
    ) -> None:
        missing = [intent.shot_id for intent in intents if intent.shot_id not in results]
        if missing:
            raise VisualGenerationBackendError(
                f"Render manager did not return results for: {', '.join(missing)}"
            )
        for intent in intents:
            result = results[intent.shot_id]
            clip_path = str(result.clip_path or "").strip()
            if not clip_path or not Path(clip_path).exists():
                raise VisualGenerationBackendError(
                    f"Rendered clip missing for shot '{intent.shot_id}'."
                )

    def _runtime_modules(self) -> _VideoRuntimeModules:
        if self._runtime_cache is not None:
            return self._runtime_cache
        try:
            cv2 = import_module("cv2")
        except ModuleNotFoundError as exc:
            raise VisualGenerationBackendError(
                "Visual backend requires opencv-python-headless to stitch generated clips."
            ) from exc
        self._runtime_cache = _VideoRuntimeModules(cv2=cv2)
        return self._runtime_cache

    def _stitch_clips(self, clip_paths: list[Path], target_path: Path) -> str:
        if not clip_paths:
            raise VisualGenerationBackendError("No clip paths were available for assembly.")

        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path and self._concat_with_ffmpeg(ffmpeg_path, clip_paths, target_path):
            return "ffmpeg"

        self._stitch_clips_opencv(clip_paths, target_path)
        return "opencv"

    def _concat_with_ffmpeg(self, ffmpeg_path: str, clip_paths: list[Path], target_path: Path) -> bool:
        manifest_path = target_path.with_suffix(".concat.txt")
        manifest_path.write_text(
            "\n".join(f"file '{path.resolve()}'" for path in clip_paths),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                ffmpeg_path,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(manifest_path),
                "-c",
                "copy",
                str(target_path),
            ],
            capture_output=True,
            text=True,
        )
        return completed.returncode == 0 and target_path.exists() and target_path.stat().st_size > 0

    def _stitch_clips_opencv(self, clip_paths: list[Path], target_path: Path) -> None:
        modules = self._runtime_modules()
        writer = None
        frame_size: tuple[int, int] | None = None
        fps = 24.0

        try:
            for clip_path in clip_paths:
                capture = modules.cv2.VideoCapture(str(clip_path))
                if not capture.isOpened():
                    raise VisualGenerationBackendError(f"Could not open generated clip: {clip_path}")
                try:
                    clip_fps = capture.get(modules.cv2.CAP_PROP_FPS)
                    if clip_fps and clip_fps > 0:
                        fps = clip_fps

                    while True:
                        ok, frame = capture.read()
                        if not ok:
                            break
                        height, width = frame.shape[:2]
                        if frame_size is None:
                            frame_size = (width, height)
                            fourcc = modules.cv2.VideoWriter_fourcc(*"mp4v")
                            writer = modules.cv2.VideoWriter(str(target_path), fourcc, fps, frame_size)
                            if not writer.isOpened():
                                raise VisualGenerationBackendError(
                                    "Could not open the final trailer writer."
                                )
                        if frame_size != (width, height):
                            frame = modules.cv2.resize(frame, frame_size)
                        writer.write(frame)
                finally:
                    capture.release()
        finally:
            if writer is not None:
                writer.release()

        if not target_path.exists() or target_path.stat().st_size <= 0:
            raise VisualGenerationBackendError("Final stitched trailer was not created.")

    def _clip_duration_seconds(self, clip_path: Path) -> float:
        modules = self._runtime_modules()
        capture = modules.cv2.VideoCapture(str(clip_path))
        if not capture.isOpened():
            raise VisualGenerationBackendError(f"Could not open rendered clip for duration read: {clip_path}")
        try:
            frames = capture.get(modules.cv2.CAP_PROP_FRAME_COUNT)
            fps = capture.get(modules.cv2.CAP_PROP_FPS) or 0.0
            if fps <= 0:
                return 0.0
            return round(float(frames / fps), 3)
        finally:
            capture.release()

    def _slug(self, value: str) -> str:
        lowered = str(value or "").strip().lower()
        slug = "".join(char if char.isalnum() else "_" for char in lowered)
        slug = slug.strip("_")
        while "__" in slug:
            slug = slug.replace("__", "_")
        return slug or "visual_render"
