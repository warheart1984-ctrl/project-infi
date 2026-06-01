"""Jarvis-native V10 Core engine with structured scene briefing and critique."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .v9_core import COMBAT_HINTS, DEFAULT_STYLE, V9CoreEngine, _utc_now


V10_TRIGGER_RE = re.compile(r"\b(v10 core|core v10)\b", re.IGNORECASE)
V10_PREFIX_RE = re.compile(
    r"^\s*(?:run|use|invoke|open|try)?\s*(?:the\s+)?(?:v10 core|core v10)\s*[:,-]?\s*",
    re.IGNORECASE,
)


def extract_v10_core_prompt(text: str | None) -> str | None:
    """Return the user payload for an explicit V10 Core request."""
    cleaned = " ".join(str(text or "").split()).strip()
    if not cleaned or not V10_TRIGGER_RE.search(cleaned):
        return None
    stripped = V10_PREFIX_RE.sub("", cleaned).strip()
    return stripped or cleaned


class V10CoreEngine(V9CoreEngine):
    """Next-gen Jarvis writing core with explicit briefing and critique stages."""

    def configure_runtime_dir(self, runtime_dir: str | Path) -> None:
        super().configure_runtime_dir(runtime_dir)
        self.memory_path = Path(runtime_dir) / "v10-core-memory.json"

    def route_angels(self, user_prompt: str, scene_brief: dict[str, Any] | None = None) -> list[str]:
        """Return the ordered V10 stage pipeline for one writing prompt."""
        normalized = str(user_prompt or "").lower()
        combat_required = bool((scene_brief or {}).get("combat_required"))
        pipeline = ["SceneAngel", "DraftAngel", "LoreAngel", "DialogueAngel", "EmotionAngel"]
        if combat_required or any(hint in normalized for hint in COMBAT_HINTS):
            pipeline.append("CombatAngel")
        pipeline.extend(["ContinuityAngel", "PacingAngel", "ToneAngel", "CriticAngel"])
        return pipeline

    def run(
        self,
        input_text: str,
        *,
        context: str = "",
        location: str = "Unknown",
        characters: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run one V10 Core pass with scene planning, revision, and critique."""
        prompt = " ".join(str(input_text or "").split()).strip()
        if not prompt:
            raise ValueError("V10 core needs a non-empty input prompt.")

        scene_context = str(context or "").strip()
        cast = [str(name).strip() for name in (characters or []) if str(name).strip()]
        memory = self._load_memory()
        style = dict(DEFAULT_STYLE)
        style.update(memory.get("style") or {})
        provider = self._resolve_provider()
        scene_brief = self._build_scene_brief(prompt, scene_context, cast, provider)
        pipeline = self.route_angels(prompt, scene_brief=scene_brief)
        logs: list[str] = [f"[SceneAngel] focus={scene_brief.get('focus', 'unknown')}"]
        notes_by_stage: dict[str, list[str]] = {}

        draft_system = (
            "You are DraftAngel inside V10 Core.\n\n"
            "Write a scene continuation that obeys the scene brief, preserves context, "
            "and ends with unresolved pressure.\n"
            "Return only the scene text."
        )
        draft_user = (
            f"SCENE BRIEF:\n{self._render_brief(scene_brief)}\n\n"
            f"CONTEXT:\n{scene_context or '(none provided)'}\n\n"
            f"PROMPT:\n{prompt}"
        )
        current_text = self._call_llm(draft_system, draft_user, provider=provider).strip()
        logs.append("[DraftAngel] complete")

        for stage in pipeline[2:-1]:
            payload = self._run_v10_pass(
                stage,
                current_text=current_text,
                scene_brief=scene_brief,
                style=style,
                characters=cast,
                provider=provider,
            )
            revised = str(payload.get("revised_text") or "").strip()
            if revised:
                current_text = revised
            stage_notes = [str(item).strip() for item in payload.get("notes", []) if str(item).strip()]
            if stage_notes:
                notes_by_stage[stage] = stage_notes
            if stage == "EmotionAngel":
                for tag in payload.get("emotion_tags", []) or []:
                    self._remember_emotion(memory, cast, tag)
            logs.append(f"[{stage}] complete")

        quality_report = self._review_scene(
            current_text=current_text,
            scene_brief=scene_brief,
            style=style,
            provider=provider,
        )
        logs.append(f"[CriticAngel] score={quality_report.get('quality_score', 'unknown')}")

        scene_entry = {
            "created_at": _utc_now(),
            "summary": prompt,
            "location": location,
            "characters": cast,
            "text": current_text,
            "pipeline": list(pipeline),
            "scene_brief": scene_brief,
            "quality_report": quality_report,
        }
        memory.setdefault("scenes", []).append(scene_entry)
        memory["last_pipeline"] = list(pipeline)
        memory["last_location"] = location
        memory["last_characters"] = list(cast)
        memory["last_scene_brief"] = scene_brief
        memory["last_quality_report"] = quality_report
        self._save_memory(memory)

        from src.aais_ul_substrate import wrap_runtime_snapshot

        return wrap_runtime_snapshot(
            {
                "status": "completed",
                "version": "v10",
                "input": prompt,
                "context": scene_context,
                "location": location,
                "characters": cast,
                "provider": provider["name"],
                "model": provider["model"],
                "scene_brief": scene_brief,
                "pipeline": pipeline,
                "output": current_text,
                "notes_by_stage": notes_by_stage,
                "quality_report": quality_report,
                "logs": logs,
                "memory_path": str(self.memory_path),
                "scene": scene_entry,
            }
        )

    def _build_scene_brief(
        self,
        prompt: str,
        context: str,
        characters: list[str],
        provider: dict[str, str],
    ) -> dict[str, Any]:
        """Generate one structured scene brief before drafting."""
        system_prompt = (
            "You are SceneAngel inside V10 Core.\n\n"
            "Turn the request into a structured scene brief.\n"
            "Return JSON with: focus, objective, tension, sensory_anchor, "
            "ending_pressure, combat_required, constraints."
        )
        user_prompt = (
            f"PROMPT:\n{prompt}\n\n"
            f"CONTEXT:\n{context or '(none provided)'}\n\n"
            f"CHARACTERS:\n{', '.join(characters) or 'Unknown'}"
        )
        try:
            payload = self._safe_json(self._call_llm(system_prompt, user_prompt, provider=provider))
        except Exception:
            payload = {}

        focus = str(payload.get("focus") or prompt[:140]).strip() or "Advance the scene clearly."
        objective = str(payload.get("objective") or "Move the scene toward a consequential emotional beat.").strip()
        tension = str(payload.get("tension") or ("high" if self._looks_conflicted(prompt, context) else "rising")).strip()
        sensory_anchor = str(payload.get("sensory_anchor") or "ash and static in the air").strip()
        ending_pressure = str(payload.get("ending_pressure") or "End with a hinge, reveal, or difficult choice.").strip()
        combat_required = bool(payload.get("combat_required")) or self._looks_combat_heavy(prompt, context)
        constraints = payload.get("constraints")
        if not isinstance(constraints, list):
            constraints = [
                "Preserve character voice.",
                "Do not contradict established context.",
                "End before the scene fully resolves.",
            ]
        constraints = [str(item).strip() for item in constraints if str(item).strip()]
        return {
            "focus": focus,
            "objective": objective,
            "tension": tension,
            "sensory_anchor": sensory_anchor,
            "ending_pressure": ending_pressure,
            "combat_required": combat_required,
            "constraints": constraints,
        }

    def _run_v10_pass(
        self,
        stage: str,
        *,
        current_text: str,
        scene_brief: dict[str, Any],
        style: dict[str, Any],
        characters: list[str],
        provider: dict[str, str],
    ) -> dict[str, Any]:
        """Run one structured V10 refinement stage."""
        prompts = {
            "LoreAngel": (
                "You are LoreAngel inside V10 Core.\n"
                "Preserve world logic and remove contradictions.\n"
                "Return JSON with revised_text and notes."
            ),
            "DialogueAngel": (
                "You are DialogueAngel inside V10 Core.\n"
                "Sharpen voice, subtext, and spoken tension.\n"
                "Return JSON with revised_text and notes."
            ),
            "EmotionAngel": (
                "You are EmotionAngel inside V10 Core.\n"
                "Deepen internal conflict and emotional clarity without altering events.\n"
                "Return JSON with revised_text, notes, and emotion_tags."
            ),
            "CombatAngel": (
                "You are CombatAngel inside V10 Core.\n"
                "Clarify motion, stakes, and physical readability.\n"
                "Return JSON with revised_text and notes."
            ),
            "ContinuityAngel": (
                "You are ContinuityAngel inside V10 Core.\n"
                "Fix timeline, POV, injury, and location drift.\n"
                "Return JSON with revised_text and notes."
            ),
            "PacingAngel": (
                "You are PacingAngel inside V10 Core.\n"
                "Tune rhythm so the scene escalates cleanly and lands on pressure.\n"
                "Return JSON with revised_text and notes."
            ),
            "ToneAngel": (
                "You are ToneAngel inside V10 Core.\n"
                f"Tone: {style.get('tone')}\n"
                f"Banned phrases: {', '.join(style.get('banned_phrases') or [])}\n"
                f"Preferred motifs: {', '.join(style.get('preferred_motifs') or [])}\n"
                "Return JSON with revised_text and notes."
            ),
        }
        system_prompt = prompts.get(stage)
        if not system_prompt:
            return {"revised_text": current_text, "notes": []}
        user_prompt = (
            f"SCENE BRIEF:\n{self._render_brief(scene_brief)}\n\n"
            f"CHARACTERS:\n{', '.join(characters) or 'Unknown'}\n\n"
            f"TEXT:\n{current_text}"
        )
        payload = self._safe_json(self._call_llm(system_prompt, user_prompt, provider=provider))
        revised_text = str(payload.get("revised_text") or current_text).strip()
        notes = payload.get("notes")
        if not isinstance(notes, list):
            notes = []
        result = {
            "revised_text": revised_text,
            "notes": [str(item).strip() for item in notes if str(item).strip()],
        }
        if stage == "EmotionAngel":
            tags = payload.get("emotion_tags")
            if isinstance(tags, list):
                result["emotion_tags"] = [str(item).strip() for item in tags if str(item).strip()]
        return result

    def _review_scene(
        self,
        *,
        current_text: str,
        scene_brief: dict[str, Any],
        style: dict[str, Any],
        provider: dict[str, str],
    ) -> dict[str, Any]:
        """Run one final critique pass and return a structured quality report."""
        system_prompt = (
            "You are CriticAngel inside V10 Core.\n"
            "Score the scene honestly and explain the strongest remaining risk.\n"
            "Return JSON with quality_score, strengths, risks, next_revision_focus, and readiness."
        )
        user_prompt = (
            f"SCENE BRIEF:\n{self._render_brief(scene_brief)}\n\n"
            f"TARGET TONE:\n{style.get('tone')}\n\n"
            f"TEXT:\n{current_text}"
        )
        try:
            payload = self._safe_json(self._call_llm(system_prompt, user_prompt, provider=provider))
        except Exception:
            payload = {}

        strengths = payload.get("strengths")
        risks = payload.get("risks")
        if not isinstance(strengths, list):
            strengths = ["Strong scene pressure.", "Clear emotional center."]
        if not isinstance(risks, list):
            risks = ["One more revision could tighten specificity."]
        return {
            "quality_score": int(payload.get("quality_score") or 78),
            "strengths": [str(item).strip() for item in strengths if str(item).strip()],
            "risks": [str(item).strip() for item in risks if str(item).strip()],
            "next_revision_focus": str(
                payload.get("next_revision_focus") or "Tighten specificity and preserve pressure in the final beat."
            ).strip(),
            "readiness": str(payload.get("readiness") or "strong_draft").strip(),
        }

    def _render_brief(self, scene_brief: dict[str, Any]) -> str:
        """Render one compact scene brief for prompt injection."""
        constraints = ", ".join(scene_brief.get("constraints") or [])
        return (
            f"Focus: {scene_brief.get('focus')}\n"
            f"Objective: {scene_brief.get('objective')}\n"
            f"Tension: {scene_brief.get('tension')}\n"
            f"Sensory anchor: {scene_brief.get('sensory_anchor')}\n"
            f"Ending pressure: {scene_brief.get('ending_pressure')}\n"
            f"Combat required: {scene_brief.get('combat_required')}\n"
            f"Constraints: {constraints}"
        )

    def _looks_conflicted(self, prompt: str, context: str) -> bool:
        normalized = f"{prompt} {context}".lower()
        return any(
            hint in normalized
            for hint in ("betrayal", "threat", "blood", "rage", "confront", "accuse", "fight", "fear")
        )

    def _looks_combat_heavy(self, prompt: str, context: str) -> bool:
        normalized = f"{prompt} {context}".lower()
        return any(hint in normalized for hint in ("fight", "battle", "attack", "combat", "duel", "sword"))


v10_core_engine = V10CoreEngine()
