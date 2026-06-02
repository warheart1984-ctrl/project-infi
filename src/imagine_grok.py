"""Grok imagine rendering for Imagine Generator — env-only xAI API keys."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.capabilities.story_forge_audio import ensure_story_forge_src

XAI_ENV_KEYS = ("STORY_FORGE_XAI_API_KEY", "XAI_API_KEY")


class KeysRequiredError(RuntimeError):
    """Raised when xAI API keys are not configured in the environment."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve_xai_api_key() -> str | None:
    for name in XAI_ENV_KEYS:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def keys_status() -> dict[str, Any]:
    return {
        "configured": resolve_xai_api_key() is not None,
        "env_vars": list(XAI_ENV_KEYS),
    }


def grok_render_path(pattern_id: str, *, imagine_root: Path | None = None) -> Path:
    from src.imagine_generator import pattern_dir

    return pattern_dir(pattern_id, root=imagine_root) / "grok_render.json"


def _hash_images(images: list[Any]) -> str:
    raw = json.dumps(images, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def grok_render_pattern(
    pattern: dict[str, Any],
    *,
    transport: Any = None,
    imagine_root: Path | None = None,
) -> dict[str, Any]:
    """Call Grok image generate using prompt_frame; requires env API key."""
    api_key = resolve_xai_api_key()
    if not api_key:
        raise KeysRequiredError(
            "xAI API key is required. Set STORY_FORGE_XAI_API_KEY or XAI_API_KEY in the environment."
        )

    ensure_story_forge_src()
    from story_forge.image_adapter.grok_adapter import GrokImageAdapter, GrokImageAdapterConfig

    adapter = GrokImageAdapter(
        GrokImageAdapterConfig(api_key=api_key),
        transport=transport,
    )
    prompt = str(pattern.get("prompt_frame") or "").strip()
    if not prompt:
        raise ValueError("prompt_frame is required for grok_render")

    result = adapter.execute(
        "generate",
        {"prompt": prompt, "n": 1, "response_format": "b64_json"},
    )
    if not result.get("ok"):
        message = result.get("message") or result.get("error_type") or "grok_render_failed"
        raise RuntimeError(str(message))

    data = dict(result.get("data") or {})
    images = data.get("images") or []
    artifact = {
        "pattern_id": pattern.get("pattern_id"),
        "imagine_generator_version": pattern.get("imagine_generator_version"),
        "provider": "xai",
        "model": result.get("model") or "grok-imagine-image",
        "image_count": len(images),
        "images_content_hash": _hash_images(images),
        "claim_label": "asserted",
        "rendered_at_utc": _utc_now_iso(),
    }
    pid = str(pattern.get("pattern_id") or "")
    if pid:
        path = grok_render_path(pid, imagine_root=imagine_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        artifact["artifact_path"] = str(path)
    return {"status": "rendered", "artifact": artifact, "adapter_result": result}


def render_grok_for_pattern(
    pattern_id: str,
    *,
    imagine_root: Path | None = None,
    transport: Any = None,
) -> dict[str, Any]:
    from src.imagine_generator import load_pattern

    pattern = load_pattern(pattern_id, root=imagine_root)
    return grok_render_pattern(pattern, transport=transport, imagine_root=imagine_root)


__all__ = [
    "KeysRequiredError",
    "XAI_ENV_KEYS",
    "grok_render_path",
    "grok_render_pattern",
    "keys_status",
    "render_grok_for_pattern",
    "resolve_xai_api_key",
]
