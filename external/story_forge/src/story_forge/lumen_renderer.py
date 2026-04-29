from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from story_forge.contracts.pipeline import (
    LUMEN_MODE_CINEMATIC,
    LUMEN_MODE_INTERACTIVE,
    TARGET_GAME,
    TARGET_MOVIE,
)
from story_forge.lumen_persona import LUMEN_DOCTRINE, LUMEN_PERSONA, lumen_can_perform
from story_forge.models import OutputPackage, Presentation, Scene, StoryRequest, StoryState, utc_now
from story_forge.visual_artifact_schema import merge_unique
from story_forge.worldpacks import get_world_pack


LUMEN_RUNTIME_LANE_ID = "lumen"
SUPPORTED_LUMEN_MODES = {
    LUMEN_MODE_CINEMATIC,
    LUMEN_MODE_INTERACTIVE,
}
OPEN_CADENCE_MARKERS = (
    "waits",
    "wait",
    "holds",
    "hold",
    "remains",
    "remain",
    "lingers",
    "linger",
    "opens",
    "open",
    "unfinished",
    "ajar",
    "yet",
    "still",
)


@dataclass(slots=True)
class LumenRenderResult:
    text: str
    audit: list[str]
    narrative_visual_recall: bool
    rendered_hooks: int
    supplemental_lines: list[str]


@dataclass(slots=True)
class LumenRenderer:
    """Deterministic doctrine-aware presentation layer."""

    version: str = "1.2-voice-doctrine"

    def render(
        self,
        state: StoryState,
        request: StoryRequest,
        package: OutputPackage,
    ) -> OutputPackage:
        if not lumen_can_perform("present_state"):
            package.presentation = Presentation(
                mode="degraded",
                provider="lumen:blocked",
                text="[LUMEN: Presentation blocked by runtime policy.]",
                approved=False,
                degraded=True,
                audit=["presentation blocked by runtime policy"],
            )
            package.state_summary["lumen"] = {
                "mode": "blocked",
                "persona": getattr(LUMEN_PERSONA, "name", "LUMEN"),
                "cartridge": getattr(state, "world_pack_id", None) or "none",
                "version": self.version,
                "style_source": "default",
                "voice_mode": LUMEN_MODE_INTERACTIVE,
                "focal_character": "",
                "doctrine_version": LUMEN_DOCTRINE.version,
                "rendered_visual_recall": False,
                "narrative_visual_recall": False,
                "rendered_hooks": 0,
            }
            return package

        base_text, base_presentation = self._get_base_text(state, package)
        world_pack = self._safe_get_world_pack(getattr(state, "world_pack_id", None))
        style = self._get_style_metadata(world_pack)
        approved_hooks = self._get_approved_presentation_hooks(package)
        visual_recall = self._get_visual_recall(package)
        active_archetype = self._format_active_archetype(getattr(state, "active_archetype", None))
        lumen_mode = self._resolve_lumen_mode(state, request, package)
        focal_character = self._resolve_focal_character(state, package)
        prior_supplemental_lines = self._prior_supplemental_lines(state)

        render_result = self._render_text(
            base_text=base_text,
            style=style,
            approved_hooks=approved_hooks,
            visual_recall=visual_recall,
            active_archetype=active_archetype,
            show_archetype=world_pack is not None,
            mode=lumen_mode,
            scene=getattr(package, "scene", None),
            request_text=request.player_input,
            prior_supplemental_lines=prior_supplemental_lines,
        )

        if base_presentation is not None:
            package.presentation = Presentation(
                mode=base_presentation.mode,
                provider=base_presentation.provider,
                text=render_result.text or base_presentation.text,
                approved=base_presentation.approved,
                degraded=base_presentation.degraded,
                audit=[*base_presentation.audit, *render_result.audit],
            )
        else:
            package.presentation = Presentation(
                mode="present",
                provider="lumen:deterministic",
                text=render_result.text or base_text,
                approved=True,
                degraded=False,
                audit=list(render_result.audit),
            )

        package.state_summary["lumen"] = {
            "mode": "deterministic",
            "persona": getattr(LUMEN_PERSONA, "name", "LUMEN"),
            "cartridge": getattr(state, "world_pack_id", None) or "none",
            "version": self.version,
            "style_source": "worldpack_metadata" if world_pack is not None else "default",
            "voice_mode": lumen_mode,
            "focal_character": focal_character or "",
            "doctrine_version": LUMEN_DOCTRINE.version,
            "rendered_visual_recall": False,
            "narrative_visual_recall": render_result.narrative_visual_recall,
            "rendered_hooks": render_result.rendered_hooks,
            "request_text": request.player_input,
        }
        self._record_render_state(
            state,
            request=request,
            mode=lumen_mode,
            focal_character=focal_character,
            result=render_result,
        )
        return package

    def _get_base_text(
        self,
        state: StoryState,
        package: OutputPackage,
    ) -> tuple[str, Presentation | None]:
        if package.presentation is not None and package.presentation.text:
            return package.presentation.text, package.presentation

        scene = getattr(package, "scene", None)
        if scene is not None:
            text = getattr(scene, "text", None)
            if text:
                return text, None

        last_scene = getattr(state, "last_scene", None)
        if last_scene is not None:
            text = getattr(last_scene, "text", None)
            if text:
                return text, None

        return "", None

    def _safe_get_world_pack(self, world_pack_id: str | None) -> Any | None:
        if not world_pack_id:
            return None
        try:
            return get_world_pack(world_pack_id)
        except Exception:
            return None

    def _get_style_metadata(self, world_pack: Any | None) -> dict[str, Any]:
        default_style = {
            "tone_prefix": "",
            "tone_suffix": "",
            "archetype_template": "The weight of {archetype} lingers.",
            "visual_recall_header": "[Visual Recall Triggered]",
            "visual_hook_template": "Hook: {hook}",
            "artifact_ids_template": "Artifacts: {artifact_ids}",
        }
        if world_pack is None:
            return default_style
        presentation = getattr(world_pack, "presentation", None)
        if isinstance(presentation, dict):
            merged = default_style.copy()
            merged.update({key: value for key, value in presentation.items() if value is not None})
            return merged
        return default_style

    def _get_visual_recall(self, package: OutputPackage) -> dict[str, Any]:
        state_summary = getattr(package, "state_summary", {}) or {}
        visual_recall = state_summary.get("visual_recall", {})
        if isinstance(visual_recall, dict):
            return visual_recall
        return {}

    def _get_approved_presentation_hooks(self, package: OutputPackage) -> list[str]:
        state_summary = getattr(package, "state_summary", {}) or {}
        hooks = state_summary.get("presentation_hooks", [])
        if isinstance(hooks, list):
            return [str(hook) for hook in hooks if str(hook).strip()]
        return []

    def _format_active_archetype(self, active_archetype: object | None) -> str | None:
        if active_archetype is None:
            return None
        if isinstance(active_archetype, str):
            value = active_archetype.strip()
            return value or None
        variant_name = str(getattr(active_archetype, "variant_name", "") or "").strip()
        archetype_type = str(getattr(active_archetype, "archetype_type", "") or "").strip()
        return variant_name or archetype_type or None

    def _resolve_lumen_mode(
        self,
        state: StoryState,
        request: StoryRequest,
        package: OutputPackage,
    ) -> str:
        state_summary = getattr(package, "state_summary", {}) or {}
        candidates = [
            state_summary.get("lumen_mode"),
            request.metadata.get("lumen_mode"),
            request.metadata.get("presentation_mode"),
            request.metadata.get("target"),
            state.runtime_lanes.get("engine_backend_import", {}).get("active_import", {}).get("lumen_mode"),
        ]
        for candidate in candidates:
            normalized = str(candidate or "").strip().lower()
            if normalized in SUPPORTED_LUMEN_MODES:
                return normalized
            if normalized == TARGET_MOVIE:
                return LUMEN_MODE_CINEMATIC
            if normalized == TARGET_GAME:
                return LUMEN_MODE_INTERACTIVE
        return LUMEN_MODE_INTERACTIVE

    def _resolve_focal_character(
        self,
        state: StoryState,
        package: OutputPackage,
    ) -> str | None:
        scene = getattr(package, "scene", None)
        if scene is not None:
            for character in getattr(scene, "characters", []) or []:
                value = str(character or "").strip()
                if value and value.lower() != "player":
                    return value
        last_scene = getattr(state, "last_scene", None)
        if last_scene is not None:
            for character in getattr(last_scene, "characters", []) or []:
                value = str(character or "").strip()
                if value and value.lower() != "player":
                    return value
        return None

    def _prior_supplemental_lines(self, state: StoryState) -> list[str]:
        lane_state = state.runtime_lanes.get(LUMEN_RUNTIME_LANE_ID, {})
        value = lane_state.get("last_supplemental_lines", [])
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    def _render_text(
        self,
        base_text: str,
        style: dict[str, Any],
        approved_hooks: list[str],
        visual_recall: dict[str, Any],
        active_archetype: str | None,
        show_archetype: bool,
        mode: str,
        scene: Scene | None,
        request_text: str,
        prior_supplemental_lines: list[str],
    ) -> LumenRenderResult:
        audit: list[str] = []
        primary_text = self._shape_primary_text(base_text, style, mode, audit)
        supplemental_lines: list[str] = []

        continuity_tokens = self._continuity_tokens(approved_hooks, visual_recall)
        continuity_line = self._build_visual_continuity_line(
            continuity_tokens=continuity_tokens,
            visual_recall=visual_recall,
            mode=mode,
        )
        if continuity_line:
            supplemental_lines.append(continuity_line)

        if show_archetype and active_archetype:
            archetype_template = str(
                style.get("archetype_template", "The weight of {archetype} lingers.")
            )
            supplemental_lines.append(archetype_template.format(archetype=active_archetype))

        bridge_line = self._build_mode_bridge_line(
            mode=mode,
            primary_text=primary_text,
            scene=scene,
            request_text=request_text,
        )
        if bridge_line:
            supplemental_lines.append(bridge_line)

        supplemental_lines = self._dedupe_supplemental_lines(
            supplemental_lines,
            prior_supplemental_lines,
        )

        lines: list[str] = []
        if primary_text:
            lines.append(primary_text)
        if supplemental_lines:
            if lines:
                lines.append("")
            lines.extend(supplemental_lines)

        return LumenRenderResult(
            text=self._collapse_silence("\n".join(lines).strip()),
            audit=audit,
            narrative_visual_recall=bool(continuity_line and continuity_line in supplemental_lines),
            rendered_hooks=len(continuity_tokens) if continuity_line and continuity_line in supplemental_lines else 0,
            supplemental_lines=supplemental_lines,
        )

    def _shape_primary_text(
        self,
        base_text: str,
        style: dict[str, Any],
        mode: str,
        audit: list[str],
    ) -> str:
        primary_text, removed_count = self._strip_prohibited_narrative_lines(base_text)
        if removed_count:
            audit.append(f"removed {removed_count} system-facing narrative line(s)")
        primary_text = self._collapse_silence(primary_text)

        if mode == LUMEN_MODE_CINEMATIC and self._contains_direct_player_address(primary_text):
            audit.append("cinematic mode retained direct player address from source text")

        tone_prefix = str(style.get("tone_prefix", "") or "")
        tone_suffix = str(style.get("tone_suffix", "") or "")
        if primary_text:
            if tone_prefix:
                primary_text = f"{tone_prefix}{primary_text}"
            if tone_suffix:
                primary_text = f"{primary_text}{tone_suffix}"
        return primary_text.strip()

    def _strip_prohibited_narrative_lines(self, text: str) -> tuple[str, int]:
        kept_lines: list[str] = []
        removed_count = 0
        for raw_line in str(text or "").replace("\r\n", "\n").split("\n"):
            stripped = raw_line.strip()
            if not stripped:
                kept_lines.append("")
                continue
            lowered = stripped.lower()
            if any(
                lowered.startswith(prefix)
                for prefix in LUMEN_DOCTRINE.prohibited_narrative_prefixes
            ):
                removed_count += 1
                continue
            kept_lines.append(stripped)
        return "\n".join(kept_lines).strip(), removed_count

    def _contains_direct_player_address(self, text: str) -> bool:
        return bool(re.search(r"\b(?:you|your)\b", text, flags=re.IGNORECASE))

    def _continuity_tokens(
        self,
        approved_hooks: list[str],
        visual_recall: dict[str, Any],
    ) -> list[str]:
        recall_hooks = visual_recall.get("hooks", [])
        recall_symbols = visual_recall.get("symbols", [])
        hooks = approved_hooks if isinstance(approved_hooks, list) else []
        recall_hook_values = recall_hooks if isinstance(recall_hooks, list) else []
        recall_symbol_values = recall_symbols if isinstance(recall_symbols, list) else []
        merged = merge_unique(hooks, recall_hook_values, recall_symbol_values)
        return [item for item in merged if str(item).strip()]

    def _build_visual_continuity_line(
        self,
        continuity_tokens: list[str],
        visual_recall: dict[str, Any],
        mode: str,
    ) -> str | None:
        if not visual_recall.get("triggered") and not continuity_tokens:
            return None

        pretty_tokens = [self._prettify_token(token) for token in continuity_tokens]
        if pretty_tokens:
            details = self._join_tokens(pretty_tokens)
            if mode == LUMEN_MODE_CINEMATIC:
                return f"The same marks remain in frame: {details}."
            return f"The remembered marks stay exact: {details}."

        if mode == LUMEN_MODE_CINEMATIC:
            return "The scene carries its prior marks forward."
        return "The scene carries its prior marks forward."

    def _build_mode_bridge_line(
        self,
        mode: str,
        primary_text: str,
        scene: Scene | None,
        request_text: str,
    ) -> str | None:
        if mode != LUMEN_MODE_INTERACTIVE or scene is None or not scene.choices:
            return None
        if self._ends_open(primary_text):
            return None

        if len(scene.choices) == 1:
            templates = (
                "One opening remains.",
                "The way forward stays narrow, but it stays open.",
                "The scene leaves one door unlatched.",
            )
        else:
            templates = (
                "More than one opening remains.",
                "The room keeps more than one door unlatched.",
                "The scene leaves more than one way forward.",
            )
        return self._stable_template_choice(
            seed=f"{request_text}|{primary_text}|{len(scene.choices)}",
            templates=templates,
        )

    def _ends_open(self, text: str) -> bool:
        lowered = str(text or "").strip().lower()
        if not lowered:
            return False
        return any(marker in lowered[-80:] for marker in OPEN_CADENCE_MARKERS)

    def _dedupe_supplemental_lines(
        self,
        lines: list[str],
        prior_lines: list[str],
    ) -> list[str]:
        seen: set[str] = set()
        prior = {line.strip() for line in prior_lines if line.strip()}
        deduped: list[str] = []
        for line in lines:
            normalized = line.strip()
            if not normalized or normalized in seen or normalized in prior:
                continue
            seen.add(normalized)
            deduped.append(normalized)
        return deduped

    def _prettify_token(self, value: str) -> str:
        return str(value or "").strip().replace("_", " ")

    def _join_tokens(self, values: list[str]) -> str:
        if not values:
            return ""
        if len(values) == 1:
            return values[0]
        if len(values) == 2:
            return f"{values[0]} and {values[1]}"
        return f"{', '.join(values[:-1])}, and {values[-1]}"

    def _stable_template_choice(
        self,
        seed: str,
        templates: tuple[str, ...],
    ) -> str:
        if not templates:
            return ""
        index = sum(ord(char) for char in seed) % len(templates)
        return templates[index]

    def _collapse_silence(self, text: str) -> str:
        collapsed = re.sub(r"\n{3,}", "\n\n", str(text or "").strip())
        return collapsed.strip()

    def _record_render_state(
        self,
        state: StoryState,
        *,
        request: StoryRequest,
        mode: str,
        focal_character: str | None,
        result: LumenRenderResult,
    ) -> None:
        state.runtime_lanes[LUMEN_RUNTIME_LANE_ID] = {
            "mode": mode,
            "focal_character": focal_character or "",
            "last_request_text": request.player_input,
            "last_text": result.text,
            "last_supplemental_lines": list(result.supplemental_lines),
            "updatedAt": utc_now(),
        }
