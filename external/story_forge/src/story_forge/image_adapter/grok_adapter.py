from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Protocol
from urllib import error, request
from urllib.parse import urlparse

from story_forge.image_adapter.base_module import (
    AAISImageModule,
    APIExecutionError,
    BoundaryExecutionError,
    InputValidationError,
    JsonDict,
    SemanticValidationError,
    encode_data_uri,
    normalize_image_bytes,
    normalize_image_reference,
)


class JsonTransport(Protocol):
    def post_json(
        self,
        url: str,
        body: JsonDict,
        headers: dict[str, str],
        timeout_seconds: float,
    ) -> JsonDict: ...


@dataclass(slots=True)
class UrllibJsonTransport:
    def post_json(
        self,
        url: str,
        body: JsonDict,
        headers: dict[str, str],
        timeout_seconds: float,
    ) -> JsonDict:
        encoded = json.dumps(body).encode("utf-8")
        http_request = request.Request(url, data=encoded, headers=headers, method="POST")
        try:
            with request.urlopen(http_request, timeout=timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            message = f"HTTP {exc.code}: {detail or exc.reason}"
            raise APIExecutionError(message) from exc
        except OSError as exc:
            raise APIExecutionError(str(exc)) from exc

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise BoundaryExecutionError("xAI image provider returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise BoundaryExecutionError("xAI image provider returned a non-object payload.")
        return payload


@dataclass(slots=True)
class GrokImageAdapterConfig:
    endpoint: str = "https://api.x.ai/v1"
    api_key: str = ""
    image_model: str = "grok-imagine-image"
    analysis_model: str = "grok-4.20-reasoning"
    timeout_seconds: float = 60.0


class GrokImageAdapter(AAISImageModule):
    def __init__(
        self,
        config: GrokImageAdapterConfig | None = None,
        *,
        transport: JsonTransport | None = None,
        logger=None,
    ) -> None:
        super().__init__(provider_name="xai", logger=logger)
        self.config = config or GrokImageAdapterConfig()
        self.transport = transport or UrllibJsonTransport()

    def _perform_action(self, action: str, payload: dict[str, Any]) -> tuple[JsonDict, str]:
        if not self.config.api_key.strip():
            raise InputValidationError("xAI API key is required.")

        normalized_action = str(action or "").strip().lower()
        if normalized_action == "generate":
            return self._perform_generate(payload), self.config.image_model
        if normalized_action == "analyze":
            return self._perform_analyze(payload), self.config.analysis_model
        if normalized_action == "edit":
            return self._perform_edit(payload), self.config.image_model
        raise InputValidationError(f"Unsupported image action '{action}'.")

    def _perform_generate(self, payload: dict[str, Any]) -> JsonDict:
        prompt = str(payload.get("prompt", "") or "").strip()
        if not prompt:
            raise InputValidationError("Image generation prompt is required.")

        n = payload.get("n", 1)
        response_format = str(payload.get("response_format", "b64_json") or "b64_json")
        self._validate_generation_options(n=n, response_format=response_format)

        body: JsonDict = {
            "model": self.config.image_model,
            "prompt": prompt,
            "n": int(n),
            "response_format": response_format.lower(),
        }
        for key in ("aspect_ratio", "quality", "seed"):
            if self._has_value(payload, key):
                body[key] = payload[key]

        response = self._post("/images/generations", body)
        return {"images": self._extract_images(response)}

    def _perform_analyze(self, payload: dict[str, Any]) -> JsonDict:
        prompt = str(payload.get("prompt", "") or "").strip()
        if not prompt:
            raise InputValidationError("Image analysis prompt is required.")

        detail = str(payload.get("detail", "low") or "low").strip().lower()
        if detail not in {"low", "high"}:
            raise InputValidationError("Image analysis detail must be 'low' or 'high'.")

        image_ref = self._resolve_image_reference(payload)
        body = {
            "model": self.config.analysis_model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image",
                            "image_url": image_ref,
                            "detail": detail,
                        },
                        {
                            "type": "input_text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        }
        response = self._post("/responses", body)
        analysis = self._extract_analysis_text(response)
        if not analysis:
            raise SemanticValidationError("Image analysis did not return any text.")
        return {"analysis": analysis}

    def _perform_edit(self, payload: dict[str, Any]) -> JsonDict:
        prompt = str(payload.get("prompt", "") or "").strip()
        if not prompt:
            raise InputValidationError("Image edit prompt is required.")

        image_ref = self._resolve_image_reference(payload)
        n = payload.get("n", 1)
        response_format = str(payload.get("response_format", "b64_json") or "b64_json")
        self._validate_generation_options(n=n, response_format=response_format)

        body: JsonDict = {
            "model": self.config.image_model,
            "prompt": prompt,
            "image": image_ref,
            "n": int(n),
            "response_format": response_format.lower(),
        }
        for key in ("aspect_ratio", "quality", "seed"):
            if self._has_value(payload, key):
                body[key] = payload[key]

        response = self._post("/images/edits", body)
        return {"images": self._extract_images(response)}

    def _post(self, path: str, body: JsonDict) -> JsonDict:
        response = self.transport.post_json(
            f"{self.config.endpoint.rstrip('/')}{path}",
            body,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout_seconds=self.config.timeout_seconds,
        )
        provider_error = response.get("error")
        if isinstance(provider_error, dict):
            message = str(provider_error.get("message", "") or provider_error)
            raise APIExecutionError(message)
        if provider_error:
            raise APIExecutionError(str(provider_error))
        return response

    def _extract_images(self, response: JsonDict) -> list[str]:
        data = response.get("data")
        if not isinstance(data, list):
            raise SemanticValidationError("Image response did not contain any images.")

        images: list[str] = []
        for item in data:
            if isinstance(item, dict):
                if self._has_value(item, "b64_json"):
                    images.append(self._coerce_image_value(item["b64_json"], source_kind="b64_json"))
                    continue
                if self._has_value(item, "url"):
                    images.append(self._coerce_image_value(item["url"], source_kind="url"))
                    continue
            if isinstance(item, str):
                images.append(self._coerce_image_value(item, source_kind="image"))

        if not images:
            raise SemanticValidationError("Image response did not contain any images.")
        return images

    def _extract_analysis_text(self, response: JsonDict) -> str:
        output_text = str(response.get("output_text", "") or "").strip()
        if output_text:
            return output_text

        outputs = response.get("output")
        if not isinstance(outputs, list):
            return ""
        texts: list[str] = []
        for item in outputs:
            if not isinstance(item, dict):
                continue
            contents = item.get("content", [])
            if not isinstance(contents, list):
                continue
            for content in contents:
                if not isinstance(content, dict):
                    continue
                if str(content.get("type", "") or "").strip() in {"output_text", "text"}:
                    text = str(content.get("text", "") or "").strip()
                    if text:
                        texts.append(text)
        return "\n".join(texts).strip()

    def _resolve_image_reference(self, payload: dict[str, Any]) -> str:
        for key in ("image", "input_image", "source_image"):
            if not self._has_value(payload, key):
                continue
            return self._resolve_single_image_value(payload[key])
        for key in ("image_url", "url"):
            if not self._has_value(payload, key):
                continue
            return self._resolve_single_image_value(payload[key])
        for key in ("image_path", "path"):
            if not self._has_value(payload, key):
                continue
            return self._path_to_data_uri(Path(str(payload[key]).strip()))
        raise InputValidationError("Image input is required.")

    def _resolve_single_image_value(self, value: Any) -> str:
        raw = str(value or "").strip()
        if not raw:
            raise InputValidationError("Image input is required.")
        if raw.startswith("data:image/"):
            return raw
        parsed = urlparse(raw)
        if parsed.scheme in {"http", "https"}:
            return raw
        return self._path_to_data_uri(Path(raw))

    def _coerce_image_value(self, raw: Any, *, source_kind: str) -> str:
        if source_kind == "b64_json":
            encoded = str(raw or "").strip()
            if not encoded:
                raise SemanticValidationError("Image response did not contain valid base64.")
            try:
                raw_bytes = base64.b64decode(encoded, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise SemanticValidationError("Image response did not contain valid base64.") from exc
            normalized_bytes, mime_type = normalize_image_bytes(
                raw_bytes,
                source_label="Image source",
            )
            return encode_data_uri(normalized_bytes, mime_type)

        value = str(raw or "").strip()
        if not value:
            raise SemanticValidationError("Image response did not contain valid image values.")
        return normalize_image_reference(value, source_label="Image source")

    def _path_to_data_uri(self, path: Path) -> str:
        if not path.exists():
            raise InputValidationError(f"Image file not found: {path}")
        if not path.is_file():
            raise InputValidationError(f"Image path is not a file: {path}")
        try:
            raw_bytes = path.read_bytes()
        except OSError as exc:
            raise BoundaryExecutionError("Image file could not be read.") from exc
        normalized_bytes, mime_type = normalize_image_bytes(raw_bytes, source_label="Image source")
        return encode_data_uri(normalized_bytes, mime_type)

    def _validate_generation_options(self, *, n: Any, response_format: Any) -> None:
        if not isinstance(n, int) or isinstance(n, bool) or int(n) <= 0:
            raise InputValidationError("Image count n must be a positive integer.")
        normalized_format = str(response_format or "").strip().lower()
        if normalized_format not in {"url", "b64_json"}:
            raise InputValidationError("Image response_format must be 'url' or 'b64_json'.")

    def _has_value(self, payload: dict[str, Any], key: str) -> bool:
        return key in payload and str(payload.get(key, "") or "").strip() != ""
