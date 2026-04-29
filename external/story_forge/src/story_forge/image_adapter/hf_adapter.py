from __future__ import annotations

import io
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from PIL import Image

from story_forge.image_adapter.base_module import (
    AAISImageModule,
    APIExecutionError,
    BoundaryExecutionError,
    InputValidationError,
    JsonDict,
    SemanticValidationError,
    decode_data_uri,
    encode_data_uri,
    normalize_image_bytes,
    normalize_image_reference,
)


class HFImageClient(Protocol):
    def text_to_image(self, prompt: str, **kwargs: Any) -> Any: ...

    def image_to_image(self, image: Any, prompt: str | None = None, **kwargs: Any) -> Any: ...

    def image_to_text(self, image: Any, **kwargs: Any) -> Any: ...


@dataclass(slots=True)
class HFImageAdapterConfig:
    api_key: str = ""
    provider: str = "auto"
    image_model: str = "black-forest-labs/FLUX.1-dev"
    edit_model: str = "black-forest-labs/FLUX.1-dev"
    analysis_model: str = ""
    timeout_seconds: float = 120.0
    default_width: int = 1024
    default_height: int = 576

    @classmethod
    def from_env(cls) -> "HFImageAdapterConfig":
        return cls(
            api_key=_env_value("STORY_FORGE_HF_TOKEN", "HF_TOKEN"),
            provider=_env_value("STORY_FORGE_HF_PROVIDER") or "auto",
            image_model=_env_value("STORY_FORGE_HF_IMAGE_MODEL") or "black-forest-labs/FLUX.1-dev",
            edit_model=_env_value("STORY_FORGE_HF_IMAGE_EDIT_MODEL")
            or _env_value("STORY_FORGE_HF_IMAGE_MODEL")
            or "black-forest-labs/FLUX.1-dev",
            analysis_model=_env_value("STORY_FORGE_HF_IMAGE_ANALYSIS_MODEL"),
        )


class HFImageAdapter(AAISImageModule):
    def __init__(
        self,
        config: HFImageAdapterConfig | None = None,
        *,
        client: HFImageClient | None = None,
        logger=None,
    ) -> None:
        super().__init__(provider_name="huggingface", logger=logger)
        self.config = config or HFImageAdapterConfig.from_env()
        self._client = client

    def _perform_action(self, action: str, payload: dict[str, Any]) -> tuple[JsonDict, str]:
        if not self.config.api_key.strip():
            raise InputValidationError("Hugging Face token is required.")

        normalized_action = str(action or "").strip().lower()
        if normalized_action == "generate":
            return self._perform_generate(payload), self.config.image_model
        if normalized_action == "analyze":
            model = self.config.analysis_model.strip() or "hf-auto-image-to-text"
            return self._perform_analyze(payload), model
        if normalized_action == "edit":
            return self._perform_edit(payload), self.config.edit_model
        raise InputValidationError(f"Unsupported image action '{action}'.")

    def _perform_generate(self, payload: dict[str, Any]) -> JsonDict:
        prompt = str(payload.get("prompt", "") or "").strip()
        if not prompt:
            raise InputValidationError("Image generation prompt is required.")

        n = payload.get("n", 1)
        response_format = str(payload.get("response_format", "b64_json") or "b64_json")
        self._validate_generation_options(n=n, response_format=response_format)

        width, height = self._resolve_dimensions(payload)
        seed = payload.get("seed")
        images: list[str] = []
        for index in range(int(n)):
            call_seed = int(seed) + index if self._has_numeric_value(seed) else None
            try:
                result = self._client_or_raise().text_to_image(
                    prompt,
                    model=self.config.image_model,
                    width=width,
                    height=height,
                    seed=call_seed,
                    guidance_scale=self._optional_float(payload, "guidance_scale"),
                    num_inference_steps=self._optional_int(payload, "num_inference_steps"),
                    scheduler=self._optional_str(payload, "scheduler"),
                    negative_prompt=self._optional_str(payload, "negative_prompt"),
                    extra_body=self._optional_dict(payload, "extra_body"),
                )
            except Exception as exc:  # noqa: BLE001 - sealed provider boundary
                raise APIExecutionError(str(exc)) from exc
            images.append(self._coerce_image_result(result, source_label="Generated image"))

        if not images:
            raise SemanticValidationError("Image response did not contain any images.")
        return {"images": images}

    def _perform_analyze(self, payload: dict[str, Any]) -> JsonDict:
        prompt = str(payload.get("prompt", "") or "").strip()
        if not prompt:
            raise InputValidationError("Image analysis prompt is required.")

        image_bytes = self._resolve_image_bytes(payload)
        try:
            result = self._client_or_raise().image_to_text(
                image_bytes,
                model=self.config.analysis_model.strip() or None,
            )
        except Exception as exc:  # noqa: BLE001 - sealed provider boundary
            raise APIExecutionError(str(exc)) from exc

        analysis = self._extract_analysis_text(result)
        if not analysis:
            raise SemanticValidationError("Image analysis did not return any text.")
        return {"analysis": analysis}

    def _perform_edit(self, payload: dict[str, Any]) -> JsonDict:
        prompt = str(payload.get("prompt", "") or "").strip()
        if not prompt:
            raise InputValidationError("Image edit prompt is required.")

        n = payload.get("n", 1)
        response_format = str(payload.get("response_format", "b64_json") or "b64_json")
        self._validate_generation_options(n=n, response_format=response_format)
        image_bytes = self._resolve_image_bytes(payload)
        width, height = self._resolve_dimensions(payload)
        target_size = self._image_target_size(width, height)
        seed = payload.get("seed")

        images: list[str] = []
        for index in range(int(n)):
            call_seed = int(seed) + index if self._has_numeric_value(seed) else None
            try:
                result = self._client_or_raise().image_to_image(
                    image_bytes,
                    prompt=prompt,
                    model=self.config.edit_model,
                    target_size=target_size,
                    seed=call_seed,
                    guidance_scale=self._optional_float(payload, "guidance_scale"),
                    num_inference_steps=self._optional_int(payload, "num_inference_steps"),
                    negative_prompt=self._optional_str(payload, "negative_prompt"),
                )
            except Exception as exc:  # noqa: BLE001 - sealed provider boundary
                raise APIExecutionError(str(exc)) from exc
            images.append(self._coerce_image_result(result, source_label="Edited image"))

        if not images:
            raise SemanticValidationError("Image response did not contain any images.")
        return {"images": images}

    def _client_or_raise(self) -> HFImageClient:
        if self._client is not None:
            return self._client
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise InputValidationError("huggingface_hub is required for Hugging Face image adapters.") from exc
        self._client = InferenceClient(
            provider=self.config.provider or "auto",
            api_key=self.config.api_key,
            timeout=self.config.timeout_seconds,
        )
        return self._client

    def _resolve_dimensions(self, payload: dict[str, Any]) -> tuple[int, int]:
        width = self._optional_int(payload, "width")
        height = self._optional_int(payload, "height")
        if width and height:
            return width, height

        aspect_ratio = str(payload.get("aspect_ratio", "") or "").strip()
        mapping = {
            "1:1": (1024, 1024),
            "16:9": (self.config.default_width, self.config.default_height),
            "9:16": (self.config.default_height, self.config.default_width),
            "4:3": (1024, 768),
            "3:4": (768, 1024),
        }
        return mapping.get(aspect_ratio, (self.config.default_width, self.config.default_height))

    def _resolve_image_bytes(self, payload: dict[str, Any]) -> bytes:
        for key in ("image", "input_image", "source_image", "image_url", "url", "image_path", "path"):
            if not self._has_value(payload, key):
                continue
            return self._image_value_to_bytes(payload[key])
        raise InputValidationError("Image input is required.")

    def _image_value_to_bytes(self, value: Any) -> bytes:
        raw = str(value or "").strip()
        if not raw:
            raise InputValidationError("Image input is required.")
        if raw.startswith("data:image/"):
            _, decoded = decode_data_uri(raw)
            normalized, _ = normalize_image_bytes(decoded, source_label="Image source")
            return normalized
        normalized_ref = normalize_image_reference(raw, source_label="Image source")
        _, decoded = decode_data_uri(normalized_ref)
        return decoded

    def _coerce_image_result(self, result: Any, *, source_label: str) -> str:
        if isinstance(result, Image.Image):
            buffer = io.BytesIO()
            result.save(buffer, format="PNG")
            raw_bytes = buffer.getvalue()
        elif isinstance(result, (bytes, bytearray, memoryview)):
            raw_bytes = bytes(result)
        elif hasattr(result, "save"):
            buffer = io.BytesIO()
            try:
                result.save(buffer, format="PNG")
            except Exception as exc:  # noqa: BLE001 - sealed provider boundary
                raise SemanticValidationError("Image response did not contain valid image values.") from exc
            raw_bytes = buffer.getvalue()
        else:
            raise SemanticValidationError("Image response did not contain valid image values.")

        normalized, mime_type = normalize_image_bytes(raw_bytes, source_label=source_label)
        return encode_data_uri(normalized, mime_type)

    def _extract_analysis_text(self, result: Any) -> str:
        if isinstance(result, str):
            return result.strip()
        if isinstance(result, dict):
            for key in ("generated_text", "text", "caption"):
                text = str(result.get(key, "") or "").strip()
                if text:
                    return text
            return ""
        generated_text = str(getattr(result, "generated_text", "") or "").strip()
        if generated_text:
            return generated_text
        text = str(getattr(result, "text", "") or "").strip()
        if text:
            return text
        return ""

    def _image_target_size(self, width: int, height: int) -> Any:
        try:
            from huggingface_hub.inference._generated.types.image_to_image import ImageToImageTargetSize
        except ImportError as exc:
            raise BoundaryExecutionError("huggingface_hub image target size type is unavailable.") from exc
        return ImageToImageTargetSize(width=width, height=height)

    def _validate_generation_options(self, *, n: Any, response_format: Any) -> None:
        if not isinstance(n, int) or isinstance(n, bool) or int(n) <= 0:
            raise InputValidationError("Image count n must be a positive integer.")
        normalized_format = str(response_format or "").strip().lower()
        if normalized_format not in {"url", "b64_json"}:
            raise InputValidationError("Image response_format must be 'url' or 'b64_json'.")

    def _optional_int(self, payload: dict[str, Any], key: str) -> int | None:
        value = payload.get(key)
        if value in (None, ""):
            return None
        if not isinstance(value, int) or isinstance(value, bool):
            raise InputValidationError(f"Image option '{key}' must be an integer.")
        return int(value)

    def _optional_float(self, payload: dict[str, Any], key: str) -> float | None:
        value = payload.get(key)
        if value in (None, ""):
            return None
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise InputValidationError(f"Image option '{key}' must be numeric.")
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
            raise InputValidationError(f"Image option '{key}' must be a dictionary.")
        return value

    def _has_numeric_value(self, value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    def _has_value(self, payload: dict[str, Any], key: str) -> bool:
        return key in payload and str(payload.get(key, "") or "").strip() != ""


def _env_value(*keys: str) -> str:
    for key in keys:
        value = os.getenv(key, "").strip()
        if value:
            return value
    return ""
