from __future__ import annotations

import base64
import binascii
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from story_forge.fal_transport import JsonTransport, UrllibJsonTransport, extract_provider_error
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


@dataclass(slots=True)
class FalImageAdapterConfig:
    endpoint: str = "https://fal.run"
    api_key: str = ""
    image_model: str = "fal-ai/glm-image"
    edit_model: str = "fal-ai/glm-image/image-to-image"
    analysis_model: str = "fal-ai/moondream3-preview/query"
    timeout_seconds: float = 180.0
    default_image_size: str = "landscape_16_9"

    @classmethod
    def from_env(cls) -> "FalImageAdapterConfig":
        return cls(
            endpoint=_env_value("STORY_FORGE_FAL_ENDPOINT") or "https://fal.run",
            api_key=_env_value("STORY_FORGE_FAL_KEY", "FAL_KEY"),
            image_model=_env_value("STORY_FORGE_FAL_IMAGE_MODEL") or "fal-ai/glm-image",
            edit_model=_env_value("STORY_FORGE_FAL_IMAGE_EDIT_MODEL") or "fal-ai/glm-image/image-to-image",
            analysis_model=_env_value("STORY_FORGE_FAL_IMAGE_ANALYSIS_MODEL")
            or "fal-ai/moondream3-preview/query",
        )


class FalImageAdapter(AAISImageModule):
    def __init__(
        self,
        config: FalImageAdapterConfig | None = None,
        *,
        transport: JsonTransport | None = None,
        logger=None,
    ) -> None:
        super().__init__(provider_name="fal", logger=logger)
        self.config = config or FalImageAdapterConfig.from_env()
        self.transport = transport or UrllibJsonTransport()

    def _perform_action(self, action: str, payload: dict[str, Any]) -> tuple[JsonDict, str]:
        if not self.config.api_key.strip():
            raise InputValidationError("fal API key is required.")

        normalized_action = str(action or "").strip().lower()
        if normalized_action == "generate":
            return self._perform_generate(payload), self.config.image_model
        if normalized_action == "analyze":
            return self._perform_analyze(payload), self.config.analysis_model
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

        body: JsonDict = {
            "prompt": prompt,
            "image_size": self._resolve_image_size(payload),
            "num_images": int(n),
            "output_format": self._resolve_output_format(payload),
            "sync_mode": self._should_sync(response_format),
            "enable_prompt_expansion": self._optional_bool(payload, "enable_prompt_expansion", default=False),
        }
        self._append_generation_options(body, payload)

        response = self._post(self.config.image_model, body)
        return {"images": self._extract_images(response)}

    def _perform_analyze(self, payload: dict[str, Any]) -> JsonDict:
        prompt = str(payload.get("prompt", "") or "").strip()
        if not prompt:
            raise InputValidationError("Image analysis prompt is required.")

        body: JsonDict = {
            "image_url": self._resolve_image_reference(payload),
            "prompt": prompt,
            "reasoning": self._optional_bool(payload, "reasoning", default=False),
        }
        temperature = self._optional_float(payload, "temperature")
        if temperature is not None:
            body["temperature"] = temperature
        top_p = self._optional_float(payload, "top_p")
        if top_p is not None:
            body["top_p"] = top_p

        response = self._post(self.config.analysis_model, body)
        analysis = self._extract_analysis_text(response)
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

        body: JsonDict = {
            "prompt": prompt,
            "image_size": self._resolve_image_size(payload),
            "num_images": int(n),
            "output_format": self._resolve_output_format(payload),
            "sync_mode": self._should_sync(response_format),
            "enable_prompt_expansion": self._optional_bool(payload, "enable_prompt_expansion", default=False),
            "image_urls": [self._resolve_image_reference(payload)],
        }
        self._append_generation_options(body, payload)

        response = self._post(self.config.edit_model, body)
        return {"images": self._extract_images(response)}

    def _append_generation_options(self, body: JsonDict, payload: dict[str, Any]) -> None:
        seed = self._optional_int(payload, "seed")
        if seed is not None:
            body["seed"] = seed
        guidance_scale = self._optional_float(payload, "guidance_scale")
        if guidance_scale is not None:
            body["guidance_scale"] = guidance_scale
        num_inference_steps = self._optional_int(payload, "num_inference_steps")
        if num_inference_steps is not None:
            body["num_inference_steps"] = num_inference_steps
        enable_safety_checker = self._optional_bool(payload, "enable_safety_checker")
        if enable_safety_checker is not None:
            body["enable_safety_checker"] = enable_safety_checker

    def _post(self, model_id: str, body: JsonDict) -> JsonDict:
        response = self.transport.post_json(
            f"{self.config.endpoint.rstrip('/')}/{model_id.lstrip('/')}",
            body,
            headers=self._headers(),
            timeout_seconds=self.config.timeout_seconds,
        )
        provider_error = extract_provider_error(response)
        if provider_error:
            raise APIExecutionError(provider_error)
        return response

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Key {self.config.api_key}",
            "Content-Type": "application/json",
        }

    def _extract_images(self, response: JsonDict) -> list[str]:
        candidates: list[Any] = [
            response.get("images"),
            response.get("data"),
            response.get("output"),
        ]
        images: list[str] = []
        for candidate in candidates:
            if not isinstance(candidate, list):
                continue
            for item in candidate:
                image = self._coerce_image_entry(item)
                if image:
                    images.append(image)
            if images:
                break

        if not images:
            raise SemanticValidationError("Image response did not contain any images.")
        return images

    def _coerce_image_entry(self, item: Any) -> str:
        if isinstance(item, str):
            return self._coerce_image_value(item)
        if not isinstance(item, dict):
            return ""
        for key in ("url", "image_url", "data_uri", "content", "b64_json"):
            value = str(item.get(key, "") or "").strip()
            if value:
                return self._coerce_image_value(value)
        return ""

    def _coerce_image_value(self, value: str) -> str:
        raw = str(value or "").strip()
        if not raw:
            raise SemanticValidationError("Image response did not contain valid image values.")
        if raw.startswith("data:image/"):
            return normalize_image_reference(raw, source_label="Image source")
        if self._looks_like_base64(raw):
            try:
                decoded = base64.b64decode(raw, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise SemanticValidationError("Image response did not contain valid base64.") from exc
            normalized, mime_type = normalize_image_bytes(decoded, source_label="Image source")
            return encode_data_uri(normalized, mime_type)
        return normalize_image_reference(raw, source_label="Image source")

    def _extract_analysis_text(self, response: JsonDict) -> str:
        for key in ("output", "text", "answer"):
            text = str(response.get(key, "") or "").strip()
            if text:
                return text
        return ""

    def _resolve_image_reference(self, payload: dict[str, Any]) -> str:
        for key in ("image", "input_image", "source_image", "image_url", "url", "image_path", "path"):
            if not self._has_value(payload, key):
                continue
            return self._coerce_input_image(payload[key])
        raise InputValidationError("Image input is required.")

    def _coerce_input_image(self, value: Any) -> str:
        raw = str(value or "").strip()
        if not raw:
            raise InputValidationError("Image input is required.")
        if raw.startswith("data:image/"):
            mime_type, decoded = decode_data_uri(raw)
            normalized, normalized_mime_type = normalize_image_bytes(decoded, source_label="Image source")
            return encode_data_uri(normalized, normalized_mime_type or mime_type)
        parsed = urlparse(raw)
        if parsed.scheme in {"http", "https"}:
            return raw
        path = Path(raw)
        if not path.exists():
            raise InputValidationError(f"Image file not found: {path}")
        if not path.is_file():
            raise InputValidationError(f"Image path is not a file: {path}")
        return normalize_image_reference(str(path), source_label="Image source")

    def _resolve_image_size(self, payload: dict[str, Any]) -> str | JsonDict:
        image_size = payload.get("image_size")
        if isinstance(image_size, str) and image_size.strip():
            return image_size.strip()
        if isinstance(image_size, dict):
            width = image_size.get("width")
            height = image_size.get("height")
            if isinstance(width, int) and not isinstance(width, bool) and isinstance(height, int) and not isinstance(height, bool):
                return {"width": int(width), "height": int(height)}
            raise InputValidationError("Image option 'image_size' must contain integer width and height.")

        width = self._optional_int(payload, "width")
        height = self._optional_int(payload, "height")
        if width is not None and height is not None:
            return {"width": width, "height": height}

        aspect_ratio = str(payload.get("aspect_ratio", "") or "").strip()
        mapping = {
            "1:1": "square_hd",
            "16:9": "landscape_16_9",
            "9:16": "portrait_16_9",
            "4:3": "landscape_4_3",
            "3:4": "portrait_4_3",
            "3:2": "landscape_3_2",
            "2:3": "portrait_3_2",
        }
        return mapping.get(aspect_ratio, self.config.default_image_size)

    def _resolve_output_format(self, payload: dict[str, Any]) -> str:
        output_format = str(payload.get("output_format", "png") or "png").strip().lower()
        if output_format not in {"jpeg", "png"}:
            raise InputValidationError("Image output_format must be 'jpeg' or 'png'.")
        return output_format

    def _should_sync(self, response_format: str) -> bool:
        return str(response_format or "").strip().lower() == "b64_json"

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

    def _optional_bool(self, payload: dict[str, Any], key: str, *, default: bool | None = None) -> bool | None:
        value = payload.get(key, default)
        if value is None:
            return None
        if not isinstance(value, bool):
            raise InputValidationError(f"Image option '{key}' must be a boolean.")
        return value

    def _has_value(self, payload: dict[str, Any], key: str) -> bool:
        return key in payload and str(payload.get(key, "") or "").strip() != ""

    def _looks_like_base64(self, value: str) -> bool:
        raw = str(value or "").strip()
        if len(raw) < 32 or (len(raw) % 4) != 0:
            return False
        if raw.startswith(("http://", "https://", "data:")):
            return False
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
        return all(char in allowed for char in raw)


def _env_value(*keys: str) -> str:
    for key in keys:
        value = os.getenv(key, "").strip()
        if value:
            return value
    return ""
