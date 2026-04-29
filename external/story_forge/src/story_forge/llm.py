from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol
from urllib import request
from urllib.parse import quote


DEFAULT_TRANSLATION_SYSTEM_PROMPT = (
    "You are Story Forge's bounded translation assistant. "
    "You may only refine the provided deterministic scene grammar from the supplied source text. "
    "You must preserve act ids, scene ids, scene order, and scene count. "
    "Do not invent scenes, characters, locations, or plot events not present in the source text. "
    "Return JSON only with a single key: scene_grammar."
)
DEFAULT_TRANSLATION_PROBE_TEXT = (
    "CHAPTER ONE\n\n"
    "Eli arrives at the archive in the rain.\n\n"
    "He finds the wrong ledger under glass."
)
LLM_ENV_FILENAME = "story_forge_llm.env"
LLM_HISTORY_LIMIT = 24
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
TRANSLATION_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "acts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "act_id": {"type": "string"},
                    "title": {"type": "string"},
                    "scenes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "scene_id": {"type": "string"},
                                "title": {"type": "string"},
                                "summary": {"type": "string"},
                                "emotional_tags": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "structural_markers": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": [
                                "scene_id",
                                "title",
                                "summary",
                                "emotional_tags",
                                "structural_markers",
                            ],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["act_id", "title", "scenes"],
                "additionalProperties": False,
            },
        },
        "emotional_tags": {
            "type": "array",
            "items": {"type": "string"},
        },
        "structural_markers": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "acts",
        "emotional_tags",
        "structural_markers",
    ],
    "additionalProperties": False,
}


@dataclass(slots=True)
class TranslationProposal:
    payload: dict[str, Any]
    provider: str
    raw: dict[str, Any] = field(default_factory=dict)


class TranslationProvider(Protocol):
    provider_name: str

    def propose_scene_grammar(self, *, prompt: str, context: dict[str, Any]) -> TranslationProposal: ...


@dataclass(slots=True)
class OpenAiCompatibleConfig:
    endpoint: str
    api_key: str
    model: str
    timeout_seconds: float = 20.0
    temperature: float = 0.1
    max_tokens: int = 700
    system_prompt: str = DEFAULT_TRANSLATION_SYSTEM_PROMPT


class OpenAiCompatibleTranslationProvider:
    provider_name = "openai_compatible_translation"

    def __init__(self, config: OpenAiCompatibleConfig) -> None:
        self.config = config

    def propose_scene_grammar(self, *, prompt: str, context: dict[str, Any]) -> TranslationProposal:
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "response_format": {"type": "json_object"},
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }
        response = request.urlopen(
            request.Request(self.config.endpoint, data=body, headers=headers, method="POST"),
            timeout=self.config.timeout_seconds,
        )
        with response:
            raw = json.loads(response.read().decode("utf-8"))
        content = _extract_completion_text(raw)
        scene_grammar = _extract_translation_refinement_payload(content)
        return TranslationProposal(
            payload=scene_grammar,
            provider=f"{self.provider_name}:{self.config.model}",
            raw=raw,
        )


class GeminiDirectTranslationProvider:
    provider_name = "gemini_direct_translation"

    def __init__(self, config: OpenAiCompatibleConfig) -> None:
        self.config = config

    def propose_scene_grammar(self, *, prompt: str, context: dict[str, Any]) -> TranslationProposal:
        endpoint = f"{GEMINI_API_BASE}/models/{quote(self.config.model, safe='')}:generateContent"
        payload = {
            "systemInstruction": {
                "parts": [{"text": self.config.system_prompt}],
            },
            "contents": [
                {
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_tokens,
                "responseMimeType": "application/json",
                "responseJsonSchema": TRANSLATION_RESPONSE_SCHEMA,
                "thinkingConfig": {
                    "thinkingBudget": 0,
                },
            },
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.config.api_key,
        }
        response = request.urlopen(
            request.Request(endpoint, data=body, headers=headers, method="POST"),
            timeout=self.config.timeout_seconds,
        )
        with response:
            raw = json.loads(response.read().decode("utf-8"))
        content = _extract_gemini_generate_content_text(raw)
        scene_grammar = _load_json_object(content)
        if not isinstance(scene_grammar, dict):
            raise ValueError("Gemini direct provider did not return a JSON object.")
        return TranslationProposal(
            payload=scene_grammar,
            provider=f"{self.provider_name}:{self.config.model}",
            raw=raw,
        )


class StoryForgeLlmRuntime:
    """Translation-only LLM runtime. Story truth remains engine-owned."""

    def __init__(
        self,
        *,
        translation_provider: TranslationProvider | None = None,
        requested: bool = False,
        config_source: str = "none",
        history_limit: int = LLM_HISTORY_LIMIT,
    ) -> None:
        self.translation_provider = translation_provider
        self.requested = requested or translation_provider is not None
        self.config_source = config_source
        self.history_limit = history_limit

    @classmethod
    def from_env(cls, *, enabled: bool) -> StoryForgeLlmRuntime | None:
        if not enabled:
            return None

        file_values, file_source = _load_llm_env_file()
        endpoint, endpoint_source = _resolve_config_value(
            "STORY_FORGE_LLM_ENDPOINT",
            file_values,
            file_source,
        )
        api_key, api_key_source = _resolve_config_value(
            "STORY_FORGE_LLM_API_KEY",
            file_values,
            file_source,
        )
        model, model_source = _resolve_config_value(
            "STORY_FORGE_LLM_MODEL",
            file_values,
            file_source,
        )
        timeout_raw, timeout_source = _resolve_config_value(
            "STORY_FORGE_LLM_TIMEOUT",
            file_values,
            file_source,
            default="20",
        )
        try:
            timeout_seconds = float(timeout_raw)
        except ValueError:
            timeout_seconds = 20.0

        translation_provider = None
        config_source = "none"
        if api_key and model:
            config = OpenAiCompatibleConfig(
                endpoint=endpoint or f"{GEMINI_API_BASE}/openai/chat/completions",
                api_key=api_key,
                model=model,
                timeout_seconds=timeout_seconds,
            )
            if _should_use_gemini_direct(endpoint=endpoint, model=model):
                translation_provider = GeminiDirectTranslationProvider(config)
            elif endpoint:
                translation_provider = OpenAiCompatibleTranslationProvider(config)
            config_source = endpoint_source or api_key_source or model_source or timeout_source or "environment"
        elif any((endpoint, api_key, model)):
            config_source = endpoint_source or api_key_source or model_source or timeout_source or "partial"

        return cls(
            translation_provider=translation_provider,
            requested=True,
            config_source=config_source,
        )

    def build_translation_lane(self):
        from story_forge.lanes.translation_lane import LlmTranslationLane

        return LlmTranslationLane(
            provider=self.translation_provider,
            requested=self.requested,
        )

    def probe_translation_provider(self) -> dict[str, Any]:
        status: dict[str, Any] = {
            "requested": self.requested,
            "configured": self.translation_provider is not None,
            "config_source": self.config_source,
            "provider": getattr(self.translation_provider, "provider_name", "none"),
            "mode": "translation_only",
            "approved": False,
            "degraded": False,
            "used": False,
            "ok": False,
            "audit": [],
        }
        if self.translation_provider is None:
            status["audit"] = ["No translation provider is configured."]
            return status

        from story_forge.contracts.translation import TranslationLaneInput

        lane = self.build_translation_lane()
        grammar = lane.run(
            TranslationLaneInput(
                raw_text=DEFAULT_TRANSLATION_PROBE_TEXT,
                title="Story Forge Provider Probe",
            )
        )
        lane_status = getattr(lane, "last_status", {})
        status.update(lane_status)
        status["config_source"] = self.config_source
        status["ok"] = bool(lane_status.get("approved")) and bool(grammar.valid)
        status["implemented"] = grammar.implemented
        status["total_scenes"] = grammar.total_scenes
        return status


def _extract_completion_text(raw: dict[str, Any]) -> str:
    choices = raw.get("choices", [])
    if not choices:
        raise ValueError("LLM provider returned no choices.")
    first = choices[0]
    message = first.get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(str(text))
        if parts:
            return "".join(parts)
    raise ValueError("LLM provider returned an unsupported completion format.")


def _extract_gemini_generate_content_text(raw: dict[str, Any]) -> str:
    candidates = raw.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini provider returned no candidates.")
    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    texts: list[str] = []
    for part in parts:
        if isinstance(part, dict):
            text = part.get("text")
            if text:
                texts.append(str(text))
    if texts:
        return "".join(texts)
    raise ValueError("Gemini provider returned no text parts.")


def _extract_scene_grammar_payload(raw_content: str) -> dict[str, Any]:
    cleaned = raw_content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    payload = _load_json_object(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("LLM translation provider did not return a JSON object.")
    scene_grammar = payload.get("scene_grammar")
    if not isinstance(scene_grammar, dict):
        raise ValueError("LLM translation provider did not return a scene_grammar object.")
    return scene_grammar


def _extract_translation_refinement_payload(raw_content: str) -> dict[str, Any]:
    cleaned = raw_content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    payload = _load_json_object(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("LLM translation provider did not return a JSON object.")
    refinement = payload.get("translation_refinement")
    if isinstance(refinement, dict):
        return refinement
    return payload


def _load_json_object(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for index, char in enumerate(text):
            if char != "{":
                continue
            try:
                payload, _ = decoder.raw_decode(text[index:])
                return payload
            except json.JSONDecodeError:
                continue
        raise


def _resolve_config_value(
    key: str,
    file_values: dict[str, str],
    file_source: str | None,
    *,
    default: str = "",
) -> tuple[str, str | None]:
    env_value = os.getenv(key, "").strip()
    if env_value:
        return env_value, "environment"
    file_value = file_values.get(key, "").strip()
    if file_value:
        return file_value, file_source
    return default, file_source if default and file_source else None


def _candidate_llm_env_paths() -> list[Path]:
    candidates: list[Path] = [Path.cwd() / LLM_ENV_FILENAME]
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / LLM_ENV_FILENAME)
    else:
        candidates.append(Path(__file__).resolve().parents[2] / LLM_ENV_FILENAME)

    ordered: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
            seen.add(resolved)
            ordered.append(resolved)
    return ordered


def _load_llm_env_file() -> tuple[dict[str, str], str | None]:
    for path in _candidate_llm_env_paths():
        if not path.exists():
            continue
        values: dict[str, str] = {}
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
        return values, str(path)
    return {}, None


def _should_use_gemini_direct(*, endpoint: str, model: str) -> bool:
    lowered_endpoint = endpoint.lower()
    lowered_model = model.lower()
    return lowered_model.startswith("gemini-") and (
        not lowered_endpoint
        or "generativelanguage.googleapis.com" in lowered_endpoint
        or lowered_endpoint.endswith("/openai/chat/completions")
    )
