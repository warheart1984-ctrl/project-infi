from __future__ import annotations

from dataclasses import dataclass
import json
import time
from pathlib import Path
from typing import Any, Protocol
from urllib import error, request
from urllib.parse import urlparse

from story_forge.image_adapter.base_module import normalize_image_reference
from story_forge.video_adapter.base_module import (
    AAISVideoModule,
    APIExecutionError,
    BoundaryExecutionError,
    InputValidationError,
    JsonDict,
    SemanticValidationError,
)


class JsonTransport(Protocol):
    def post_json(
        self,
        url: str,
        body: JsonDict,
        headers: dict[str, str],
        timeout_seconds: float,
    ) -> JsonDict: ...

    def get_json(
        self,
        url: str,
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
        return self._load_json(http_request, timeout_seconds)

    def get_json(
        self,
        url: str,
        headers: dict[str, str],
        timeout_seconds: float,
    ) -> JsonDict:
        http_request = request.Request(url, headers=headers, method="GET")
        return self._load_json(http_request, timeout_seconds)

    def _load_json(self, http_request: request.Request, timeout_seconds: float) -> JsonDict:
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
            raise BoundaryExecutionError("xAI video provider returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise BoundaryExecutionError("xAI video provider returned a non-object payload.")
        return payload


@dataclass(slots=True)
class GrokVideoAdapterConfig:
    endpoint: str = "https://api.x.ai/v1"
    api_key: str = ""
    model: str = "grok-imagine-video"
    timeout_seconds: float = 60.0
    poll_interval_seconds: float = 5.0
    max_wait_seconds: float = 900.0


class GrokVideoAdapter(AAISVideoModule):
    def __init__(
        self,
        config: GrokVideoAdapterConfig | None = None,
        *,
        transport: JsonTransport | None = None,
        logger=None,
        sleeper=None,
    ) -> None:
        super().__init__(provider_name="xai", logger=logger)
        self.config = config or GrokVideoAdapterConfig()
        self.transport = transport or UrllibJsonTransport()
        self._sleeper = sleeper or time.sleep

    def _perform_action(self, action: str, payload: dict[str, Any]) -> tuple[JsonDict, str]:
        if not self.config.api_key.strip():
            raise InputValidationError("xAI API key is required.")

        normalized_action = str(action or "").strip().lower()
        if normalized_action == "generate":
            return self._perform_generate(payload), self.config.model
        if normalized_action == "status":
            return self._perform_status(payload), self.config.model
        raise InputValidationError(f"Unsupported video action '{action}'.")

    def _perform_generate(self, payload: dict[str, Any]) -> JsonDict:
        prompt = str(payload.get("prompt", "") or "").strip()
        if not prompt:
            raise InputValidationError("Video generation prompt is required.")

        duration = payload.get("duration", 5)
        if not isinstance(duration, int) or isinstance(duration, bool) or int(duration) <= 0:
            raise InputValidationError("Video duration must be a positive integer number of seconds.")

        body: JsonDict = {
            "model": self.config.model,
            "prompt": prompt,
            "duration": int(duration),
        }
        for key in ("aspect_ratio", "resolution", "seed"):
            if self._has_value(payload, key):
                body[key] = payload[key]
        image_reference = self._resolve_image_reference(payload)
        if image_reference is not None:
            body["image"] = {
                "url": image_reference,
            }

        kickoff = self._post("/videos/generations", body)
        request_id = self._extract_request_id(kickoff)
        if not request_id:
            raise SemanticValidationError("Video provider did not return a request id.")
        status_payload = self._poll_until_terminal(request_id)
        status = self._extract_status(status_payload)
        video_url = self._extract_video_url(status_payload)
        if not video_url:
            raise SemanticValidationError("Video response did not contain a renderable video URL.")
        return {
            "request_id": request_id,
            "status": status,
            "videos": [video_url],
            "duration": int(duration),
        }

    def _perform_status(self, payload: dict[str, Any]) -> JsonDict:
        request_id = str(payload.get("request_id", "") or "").strip()
        if not request_id:
            raise InputValidationError("Video request_id is required.")
        status_payload = self._get(f"/videos/generations/{request_id}")
        return {
            "request_id": request_id,
            "status": self._extract_status(status_payload),
            "videos": [self._extract_video_url(status_payload)] if self._extract_video_url(status_payload) else [],
        }

    def _poll_until_terminal(self, request_id: str) -> JsonDict:
        elapsed = 0.0
        while elapsed <= self.config.max_wait_seconds:
            payload = self._get(f"/videos/generations/{request_id}")
            status = self._extract_status(payload)
            if status in {"completed", "succeeded", "ready", "done"}:
                return payload
            if status in {"failed", "error", "cancelled", "canceled", "expired"}:
                message = self._extract_error_message(payload) or f"Video generation ended with status '{status}'."
                raise APIExecutionError(message)
            self._sleeper(self.config.poll_interval_seconds)
            elapsed += self.config.poll_interval_seconds
        raise BoundaryExecutionError("Video generation timed out.")

    def _extract_status(self, payload: JsonDict) -> str:
        for key in ("status", "state"):
            value = str(payload.get(key, "") or "").strip().lower()
            if value:
                return value
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("status", "state"):
                value = str(data.get(key, "") or "").strip().lower()
                if value:
                    return value
        return "unknown"

    def _extract_request_id(self, payload: JsonDict) -> str:
        for key in ("request_id", "id"):
            value = str(payload.get(key, "") or "").strip()
            if value:
                return value
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("request_id", "id"):
                value = str(data.get(key, "") or "").strip()
                if value:
                    return value
        return ""

    def _extract_video_url(self, payload: JsonDict) -> str:
        candidates: list[Any] = [
            payload,
            payload.get("data", {}),
            payload.get("video", {}),
            payload.get("result", {}),
            payload.get("output", {}),
        ]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            for key in ("video_url", "url"):
                value = str(candidate.get(key, "") or "").strip()
                if value:
                    return value
            videos = candidate.get("videos")
            if isinstance(videos, list):
                for item in videos:
                    if isinstance(item, str) and item.strip():
                        return item.strip()
                    if isinstance(item, dict):
                        value = str(item.get("url", "") or "").strip()
                        if value:
                            return value
        return ""

    def _extract_error_message(self, payload: JsonDict) -> str:
        provider_error = payload.get("error")
        if isinstance(provider_error, dict):
            return str(provider_error.get("message", "") or provider_error)
        if provider_error:
            return str(provider_error)
        return ""

    def _resolve_image_reference(self, payload: dict[str, Any]) -> str | None:
        for key in ("image", "image_url", "source_image"):
            if not self._has_value(payload, key):
                continue
            raw = str(payload[key]).strip()
            if raw.startswith("data:image/"):
                return raw
            parsed = urlparse(raw)
            if parsed.scheme in {"http", "https"}:
                return raw
            return normalize_image_reference(raw, source_label="Image source")
        for key in ("image_path", "path"):
            if not self._has_value(payload, key):
                continue
            return normalize_image_reference(str(Path(str(payload[key]).strip())), source_label="Image source")
        return None

    def _post(self, path: str, body: JsonDict) -> JsonDict:
        payload = self.transport.post_json(
            f"{self.config.endpoint.rstrip('/')}{path}",
            body,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout_seconds=self.config.timeout_seconds,
        )
        provider_error = payload.get("error")
        if isinstance(provider_error, dict):
            raise APIExecutionError(str(provider_error.get("message", "") or provider_error))
        if provider_error:
            raise APIExecutionError(str(provider_error))
        return payload

    def _get(self, path: str) -> JsonDict:
        payload = self.transport.get_json(
            f"{self.config.endpoint.rstrip('/')}{path}",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout_seconds=self.config.timeout_seconds,
        )
        provider_error = payload.get("error")
        if isinstance(provider_error, dict):
            raise APIExecutionError(str(provider_error.get("message", "") or provider_error))
        if provider_error:
            raise APIExecutionError(str(provider_error))
        return payload

    def _has_value(self, payload: dict[str, Any], key: str) -> bool:
        return key in payload and str(payload.get(key, "") or "").strip() != ""
