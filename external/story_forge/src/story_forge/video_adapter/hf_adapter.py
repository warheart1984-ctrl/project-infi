from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from story_forge.image_adapter.base_module import (
    APIExecutionError,
    BoundaryExecutionError,
    InputValidationError,
    decode_data_uri,
    encode_data_uri,
    normalize_image_bytes,
    normalize_image_reference,
)
from story_forge.video_adapter.base_module import (
    AAISVideoModule,
    JsonDict,
    SemanticValidationError,
)


class HFVideoClient(Protocol):
    def text_to_video(self, prompt: str, **kwargs: Any) -> bytes: ...

    def image_to_video(self, image: Any, **kwargs: Any) -> bytes: ...


@dataclass(slots=True)
class HFVideoAdapterConfig:
    api_key: str = ""
    provider: str = "auto"
    text_to_video_model: str = "Wan-AI/Wan2.2-T2V-A14B"
    image_to_video_model: str = "Wan-AI/Wan2.2-I2V-A14B"
    timeout_seconds: float = 600.0
    frames_per_second: float = 12.0
    default_width: int = 1280
    default_height: int = 720

    @classmethod
    def from_env(cls) -> "HFVideoAdapterConfig":
        return cls(
            api_key=_env_value("STORY_FORGE_HF_TOKEN", "HF_TOKEN"),
            provider=_env_value("STORY_FORGE_HF_PROVIDER") or "auto",
            text_to_video_model=_env_value("STORY_FORGE_HF_TEXT_TO_VIDEO_MODEL") or "Wan-AI/Wan2.2-T2V-A14B",
            image_to_video_model=_env_value("STORY_FORGE_HF_IMAGE_TO_VIDEO_MODEL")
            or "Wan-AI/Wan2.2-I2V-A14B",
        )


class HFVideoAdapter(AAISVideoModule):
    def __init__(
        self,
        config: HFVideoAdapterConfig | None = None,
        *,
        client: HFVideoClient | None = None,
        logger=None,
    ) -> None:
        super().__init__(provider_name="huggingface", logger=logger)
        self.config = config or HFVideoAdapterConfig.from_env()
        self._client = client

    def _perform_action(self, action: str, payload: dict[str, Any]) -> tuple[JsonDict, str]:
        if not self.config.api_key.strip():
            raise InputValidationError("Hugging Face token is required.")

        normalized_action = str(action or "").strip().lower()
        if normalized_action == "generate":
            model = self.config.image_to_video_model if self._has_image_input(payload) else self.config.text_to_video_model
            return self._perform_generate(payload), model
        if normalized_action == "status":
            raise InputValidationError("Hugging Face video adapter does not support async status lookup.")
        raise InputValidationError(f"Unsupported video action '{action}'.")

    def _perform_generate(self, payload: dict[str, Any]) -> JsonDict:
        prompt = str(payload.get("prompt", "") or "").strip()
        if not prompt:
            raise InputValidationError("Video generation prompt is required.")

        duration = payload.get("duration", 5)
        if not isinstance(duration, int) or isinstance(duration, bool) or int(duration) <= 0:
            raise InputValidationError("Video duration must be a positive integer number of seconds.")

        num_frames = max(8, int(round(int(duration) * self.config.frames_per_second)))
        target_size = self._video_target_size(*self._resolve_dimensions(payload))
        seed = self._optional_int(payload, "seed")

        try:
            if self._has_image_input(payload):
                video_bytes = self._client_or_raise().image_to_video(
                    self._resolve_image_bytes(payload),
                    model=self.config.image_to_video_model,
                    prompt=prompt,
                    num_frames=num_frames,
                    seed=seed,
                    guidance_scale=self._optional_float(payload, "guidance_scale"),
                    num_inference_steps=self._optional_int(payload, "num_inference_steps"),
                    negative_prompt=self._optional_str(payload, "negative_prompt"),
                    target_size=target_size,
                )
            else:
                negative_prompt = self._optional_str(payload, "negative_prompt")
                negative_prompts = [negative_prompt] if negative_prompt else None
                video_bytes = self._client_or_raise().text_to_video(
                    prompt,
                    model=self.config.text_to_video_model,
                    num_frames=num_frames,
                    seed=seed,
                    guidance_scale=self._optional_float(payload, "guidance_scale"),
                    num_inference_steps=self._optional_int(payload, "num_inference_steps"),
                    negative_prompt=negative_prompts,
                    extra_body=self._optional_dict(payload, "extra_body"),
                )
        except Exception as exc:  # noqa: BLE001 - sealed provider boundary
            raise APIExecutionError(str(exc)) from exc

        encoded_video = self._coerce_video_result(video_bytes)
        return {
            "status": "completed",
            "videos": [encoded_video],
            "duration": int(duration),
        }

    def _client_or_raise(self) -> HFVideoClient:
        if self._client is not None:
            return self._client
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise InputValidationError("huggingface_hub is required for Hugging Face video adapters.") from exc
        self._client = InferenceClient(
            provider=self.config.provider or "auto",
            api_key=self.config.api_key,
            timeout=self.config.timeout_seconds,
        )
        return self._client

    def _coerce_video_result(self, result: Any) -> str:
        if not isinstance(result, (bytes, bytearray, memoryview)):
            raise SemanticValidationError("Video response did not contain a renderable video.")
        raw_bytes = bytes(result)
        if not raw_bytes:
            raise SemanticValidationError("Video response did not contain a renderable video.")
        return encode_data_uri(raw_bytes, "video/mp4")

    def _resolve_dimensions(self, payload: dict[str, Any]) -> tuple[int, int]:
        resolution = str(payload.get("resolution", "") or "").strip().lower()
        aspect_ratio = str(payload.get("aspect_ratio", "16:9") or "16:9").strip()
        if resolution == "1080p":
            return (1920, 1080) if aspect_ratio == "16:9" else (1080, 1920)
        if resolution == "720p":
            return (1280, 720) if aspect_ratio == "16:9" else (720, 1280)
        return (self.config.default_width, self.config.default_height)

    def _resolve_image_bytes(self, payload: dict[str, Any]) -> bytes:
        for key in ("image", "image_url", "source_image", "image_path", "path"):
            if not self._has_value(payload, key):
                continue
            return self._image_value_to_bytes(payload[key])
        raise InputValidationError("Video image input is required.")

    def _image_value_to_bytes(self, value: Any) -> bytes:
        raw = str(value or "").strip()
        if not raw:
            raise InputValidationError("Video image input is required.")
        if raw.startswith("data:image/"):
            _, decoded = decode_data_uri(raw)
            normalized, _ = normalize_image_bytes(decoded, source_label="Image source")
            return normalized
        normalized_ref = normalize_image_reference(raw, source_label="Image source")
        _, decoded = decode_data_uri(normalized_ref)
        return decoded

    def _video_target_size(self, width: int, height: int) -> Any:
        try:
            from huggingface_hub.inference._generated.types.image_to_video import ImageToVideoTargetSize
        except ImportError as exc:
            raise BoundaryExecutionError("huggingface_hub video target size type is unavailable.") from exc
        return ImageToVideoTargetSize(width=width, height=height)

    def _optional_int(self, payload: dict[str, Any], key: str) -> int | None:
        value = payload.get(key)
        if value in (None, ""):
            return None
        if not isinstance(value, int) or isinstance(value, bool):
            raise InputValidationError(f"Video option '{key}' must be an integer.")
        return int(value)

    def _optional_float(self, payload: dict[str, Any], key: str) -> float | None:
        value = payload.get(key)
        if value in (None, ""):
            return None
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise InputValidationError(f"Video option '{key}' must be numeric.")
        return float(value)

    def _optional_str(self, payload: dict[str, Any], key: str) -> str | None:
        if not self._has_value(payload, key):
            return None
        return str(payload[key]).strip()

    def _optional_dict(self, payload: dict[str, Any], key: str) -> dict[str, Any] | None:
        value = payload.get(key)
        if value in (None, ""):
            return None
        if not isinstance(value, dict):
            raise InputValidationError(f"Video option '{key}' must be a dictionary.")
        return value

    def _has_image_input(self, payload: dict[str, Any]) -> bool:
        return any(self._has_value(payload, key) for key in ("image", "image_url", "source_image", "image_path", "path"))

    def _has_value(self, payload: dict[str, Any], key: str) -> bool:
        return key in payload and str(payload.get(key, "") or "").strip() != ""


def _env_value(*keys: str) -> str:
    for key in keys:
        value = os.getenv(key, "").strip()
        if value:
            return value
    return ""
