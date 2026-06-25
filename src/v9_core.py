"""Jarvis-native V9 Core engine adapted from the older Divine Core pipeline."""

from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
import json
import os
from pathlib import Path
import re
from typing import Any

import requests


DEFAULT_CANON = (
    "Preserve established world logic, emotional continuity, physical clarity, "
    "and character voice. Do not invent contradictory lore."
)

DEFAULT_STYLE = {
    "tone": "dark, lyrical, intimate, emotionally charged",
    "banned_phrases": [
        "everything changed",
        "for the first time",
        "heart pounding",
    ],
    "preferred_motifs": [
        "ash",
        "veil",
        "longing",
        "dread",
        "heat",
    ],
}

COMBAT_HINTS = ("fight", "battle", "attack", "combat", "duel", "sword")
V9_TRIGGER_RE = re.compile(r"\b(v9 core|divine core)\b", re.IGNORECASE)
V9_PREFIX_RE = re.compile(
    r"^\s*(?:run|use|invoke|open|try)?\s*(?:the\s+)?(?:v9 core|divine core)\s*[:,-]?\s*",
    re.IGNORECASE,
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def extract_v9_core_prompt(text: str | None) -> str | None:
    """Return the user payload for an explicit V9 Core request."""
    cleaned = " ".join(str(text or "").split()).strip()
    if not cleaned or not V9_TRIGGER_RE.search(cleaned):
        return None
    stripped = V9_PREFIX_RE.sub("", cleaned).strip()
    return stripped or cleaned


class V9CoreEngine:
    """Run the old multi-angel writing pipeline inside the Jarvis tool layer."""

    def __init__(self, runtime_dir: str | Path | None = None) -> None:
        self.configure_runtime_dir(runtime_dir or Path.cwd() / ".runtime")

    def configure_runtime_dir(self, runtime_dir: str | Path) -> None:
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.memory_path = self.runtime_dir / "v9-core-memory.json"

    def route_angels(self, user_prompt: str) -> list[str]:
        """Return the ordered angel pipeline for one writing prompt."""
        normalized = str(user_prompt or "").lower()
        pipeline = ["DraftAngel", "LoreAngel"]
        if any(hint in normalized for hint in COMBAT_HINTS):
            pipeline.append("CombatAngel")
        pipeline.extend(
            [
                "DialogueAngel",
                "EmotionAngel",
                "ContinuityAngel",
                "PacingAngel",
                "ToneAngel",
            ]
        )
        return pipeline

    def run(
        self,
        input_text: str,
        *,
        context: str = "",
        location: str = "Unknown",
        characters: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run one V9 Core pass and persist lightweight scene memory."""
        prompt = " ".join(str(input_text or "").split()).strip()
        if not prompt:
            raise ValueError("V9 core needs a non-empty input prompt.")

        scene_context = str(context or "").strip()
        cast = [str(name).strip() for name in (characters or []) if str(name).strip()]
        memory = self._load_memory()
        canon = str(memory.get("canon") or DEFAULT_CANON)
        style = dict(DEFAULT_STYLE)
        style.update(memory.get("style") or {})
        pipeline = self.route_angels(prompt)
        provider = self._resolve_provider()
        logs: list[str] = [f"[Router] {' -> '.join(pipeline)}"]

        draft_system = (
            "You are DraftAngel.\n\n"
            "Continue the scene using only the context and prompt.\n"
            "Produce raw narrative without commentary.\n"
            "Return only the continuation text."
        )
        draft_user = f"CONTEXT:\n{scene_context or '(none provided)'}\n\nPROMPT:\n{prompt}"
        current_text = self._call_llm(draft_system, draft_user, provider=provider).strip()
        logs.append("[DraftAngel] complete")
        notes_by_angel: dict[str, list[str]] = {}

        for angel in pipeline[1:]:
            payload = self._run_angel_pass(
                angel,
                current_text=current_text,
                canon=canon,
                style=style,
                characters=cast,
                provider=provider,
            )
            revised = str(payload.get("revised_text") or "").strip()
            if revised:
                current_text = revised
            angel_notes = [str(item).strip() for item in payload.get("notes", []) if str(item).strip()]
            if angel_notes:
                notes_by_angel[angel] = angel_notes
            if angel == "EmotionAngel":
                for tag in payload.get("emotion_tags", []) or []:
                    self._remember_emotion(memory, cast, tag)
            logs.append(f"[{angel}] complete")

        scene_entry = {
            "created_at": _utc_now(),
            "summary": prompt,
            "location": location,
            "characters": cast,
            "text": current_text,
            "pipeline": list(pipeline),
        }
        memory.setdefault("scenes", []).append(scene_entry)
        memory["last_pipeline"] = list(pipeline)
        memory["last_location"] = location
        memory["last_characters"] = list(cast)
        self._save_memory(memory)

        from src.aais_ul.runtime import wrap_runtime_snapshot

        return wrap_runtime_snapshot(
            {
                "status": "completed",
                "input": prompt,
                "context": scene_context,
                "location": location,
                "characters": cast,
                "provider": provider["name"],
                "model": provider["model"],
                "pipeline": pipeline,
                "output": current_text,
                "notes_by_angel": notes_by_angel,
                "logs": logs,
                "memory_path": str(self.memory_path),
                "scene": scene_entry,
            }
        )

    def _default_memory(self) -> dict[str, Any]:
        return {
            "canon": DEFAULT_CANON,
            "style": dict(DEFAULT_STYLE),
            "scenes": [],
            "character_emotions": {},
            "last_pipeline": [],
        }

    def _load_memory(self) -> dict[str, Any]:
        if not self.memory_path.exists():
            return self._default_memory()
        try:
            return json.loads(self.memory_path.read_text(encoding="utf-8"))
        except Exception:
            return self._default_memory()

    def _save_memory(self, memory: dict[str, Any]) -> None:
        self.memory_path.write_text(
            json.dumps(memory, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _remember_emotion(self, memory: dict[str, Any], characters: list[str], tag: str) -> None:
        registry = memory.setdefault("character_emotions", {})
        for character in characters:
            history = list(registry.get(character) or [])
            if tag not in history:
                history.append(tag)
            registry[character] = history[-8:]

    def _resolve_provider(self) -> dict[str, str]:
        llm_url = str(os.getenv("LLM_API_URL") or "").strip()
        llm_model = str(os.getenv("LLM_MODEL_NAME") or "").strip()
        llm_key = str(os.getenv("LLM_API_KEY") or "").strip()
        if llm_url:
            return {
                "name": "custom_llm",
                "url": llm_url,
                "model": llm_model or "default",
                "api_key": llm_key,
            }

        openrouter_key = str(os.getenv("OPENROUTER_API_KEY") or "").strip()
        if openrouter_key:
            return {
                "name": "openrouter",
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "model": str(os.getenv("AAIS_OPENROUTER_MODEL") or "openrouter/free").strip(),
                "api_key": openrouter_key,
            }

        raise RuntimeError(
            "V9 core is not configured. Set LLM_API_URL/LLM_MODEL_NAME or OPENROUTER_API_KEY."
        )

    def _call_llm(self, system_prompt: str, user_prompt: str, *, provider: dict[str, str]) -> str:
        headers = {"Content-Type": "application/json"}
        api_key = str(provider.get("api_key") or "").strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": provider["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        response = requests.post(provider["url"], json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        if isinstance(data.get("message"), dict) and isinstance(data["message"].get("content"), str):
            return data["message"]["content"]
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message") or {}
            if isinstance(message.get("content"), str):
                return message["content"]
        raise RuntimeError("V9 core provider returned an unexpected response shape.")

    def _run_angel_pass(
        self,
        angel: str,
        *,
        current_text: str,
        canon: str,
        style: dict[str, Any],
        characters: list[str],
        provider: dict[str, str],
    ) -> dict[str, Any]:
        prompts = {
            "LoreAngel": (
                "You are LoreAngel.\n\n"
                "Enforce canon and fix contradictions with minimal edits.\n"
                f"CANON:\n{canon}\n\n"
                "Return JSON with revised_text and optional notes."
            ),
            "CombatAngel": (
                "You are CombatAngel.\n\n"
                "Clarify physical action and pacing without changing outcomes.\n"
                f"CANON:\n{canon}\n\n"
                "Return JSON with revised_text and optional notes."
            ),
            "DialogueAngel": (
                "You are DialogueAngel.\n\n"
                "Sharpen dialogue, preserve character voice, and remove filler.\n"
                "Return JSON with revised_text and optional notes."
            ),
            "EmotionAngel": (
                "You are EmotionAngel.\n\n"
                "Deepen emotional realism and subtext without changing plot.\n"
                f"CHARACTERS:\n{', '.join(characters) or 'Unknown'}\n\n"
                "Return JSON with revised_text, optional notes, and emotion_tags."
            ),
            "ContinuityAngel": (
                "You are ContinuityAngel.\n\n"
                "Fix timeline, POV, injury, clothing, and continuity drift.\n"
                "Return JSON with revised_text and optional notes."
            ),
            "PacingAngel": (
                "You are PacingAngel.\n\n"
                "Adjust rhythm and tension with minimal edits.\n"
                "Return JSON with revised_text and optional notes."
            ),
            "ToneAngel": (
                "You are ToneAngel.\n\n"
                f"Tone: {style.get('tone')}\n"
                f"Banned phrases: {', '.join(style.get('banned_phrases') or [])}\n"
                f"Preferred motifs: {', '.join(style.get('preferred_motifs') or [])}\n\n"
                "Enforce the requested style and return JSON with revised_text and optional notes."
            ),
        }
        system_prompt = prompts.get(angel)
        if not system_prompt:
            return {"revised_text": current_text, "notes": []}
        raw = self._call_llm(system_prompt, f"TEXT:\n{current_text}", provider=provider)
        payload = self._safe_json(raw)
        revised_text = str(payload.get("revised_text") or current_text).strip()
        notes = payload.get("notes")
        if not isinstance(notes, list):
            notes = []
        result = {
            "revised_text": revised_text,
            "notes": [str(item).strip() for item in notes if str(item).strip()],
        }
        if angel == "EmotionAngel":
            tags = payload.get("emotion_tags")
            if isinstance(tags, list):
                result["emotion_tags"] = [str(item).strip() for item in tags if str(item).strip()]
        return result

    def _safe_json(self, text: str) -> dict[str, Any]:
        cleaned = str(text or "").strip()
        if cleaned.startswith("```"):
            lines = [line for line in cleaned.splitlines() if not line.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()
        try:
            payload = json.loads(cleaned)
            return payload if isinstance(payload, dict) else {"revised_text": str(text or "")}
        except Exception:
            return {"revised_text": str(text or "")}


v9_core_engine = V9CoreEngine()
