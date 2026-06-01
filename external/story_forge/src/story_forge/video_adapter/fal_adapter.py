from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from story_forge.fal_transport import (
    JsonTransport,
    UrllibJsonTransport,
    extract_provider_error,
    with_query,
)
from story_forge.image_adapter.base_module import normalize_image_reference
from story_forge.video_adapter.base_module import (
    AAISVideoModule,
    APIExecutionError,
    BoundaryExecutionError,
    InputValidationError,
    JsonDict,
    SemanticValidationError,
)


@dataclass(slots=True)
class FalVideoAdapterConfig:
    queue_endpoint: str = "https://queue.fal.run"
    api_key: str = ""
    text_to_video_model: str = "fal-ai/hunyuan-video"
    image_to_video_model: str = "fal-ai/hunyuan-video-image-to-video"
    timeout_seconds: float = 120.0
    poll_interval_seconds: float = 5.0
    max_wait_seconds: float = 900.0
    default_resolution: str = "720p"
    frames_per_second: float = 24.0

    @classmethod
    def from_env(cls) -> "FalVideoAdapterConfig":
        return cls(
            queue_endpoint=_env_value("STORY_FORGE_FAL_QUEUE_ENDPOINT") or "https://queue.fal.run",
            api_key=_env_value("STORY_FORGE_FAL_KEY", "FAL_KEY"),
            text_to_video_model=_env_value("STORY_FORGE_FAL_TEXT_TO_VIDEO_MODEL") or "fal-ai/hunyuan-video",
            image_to_video_model=_env_value("STORY_FORGE_FAL_IMAGE_TO_VIDEO_MODEL")
            or "fal-ai/hunyuan-video-image-to-video",
        )


class FalVideoAdapter(AAISVideoModule):
    def __init__(
        self,
        config: FalVideoAdapterConfig | None = None,
        *,
        transport: JsonTransport | None = None,
        logger=None,
        sleeper=None,
    ) -> None:
        super().__init__(provider_name="fal", logger=logger)
        self.config = config or FalVideoAdapterConfig.from_env()
        self.transport = transport or UrllibJsonTransport()
        self._sleeper = sleeper or time.sleep

    def _perform_action(self, action: str, payload: dict[str, Any]) -> tuple[JsonDict, str]:
        if not self.config.api_key.strip():
            raise InputValidationError("fal API key is required.")

        normalized_action = str(action or "").strip().lower()
        if normalized_action == "generate":
            model_id = self._select_model_id(payload)
            return self._perform_generate(payload, model_id=model_id), model_id
        if normalized_action == "status":
            model_id = self._status_model_id(payload)
            return self._perform_status(payload, model_id=model_id), model_id
        raise InputValidationError(f"Unsupported video action '{action}'.")

    def _perform_generate(self, payload: dict[str, Any], *, model_id: str) -> JsonDict:
        prompt = str(payload.get("prompt", "") or "").strip()
        if not prompt:
            raise InputValidationError("Video generation prompt is required.")

        duration = payload.get("duration", 5)
        if not isinstance(duration, int) or isinstance(duration, bool) or int(duration) <= 0:
            raise InputValidationError("Video duration must be a positive integer number of seconds.")

        body: JsonDict = {
            "prompt": prompt,
            "aspect_ratio": self._resolve_aspect_ratio(payload),
            "resolution": self._resolve_resolution(payload),
            "num_frames": self._resolve_num_frames(payload, duration=int(duration)),
        }
        seed = self._optional_int(payload, "seed")
        if seed is not None:
            body["seed"] = seed
        pro_mode = self._optional_bool(payload, "pro_mode")
        if pro_mode is not None:
            body["pro_mode"] = pro_mode
        enable_safety_checker = self._optional_bool(payload, "enable_safety_checker")
        if enable_safety_checker is not None:
            body["enable_safety_checker"] = enable_safety_checker

        if self._has_image_input(payload):
            body["image_url"] = self._resolve_image_reference(payload)

        submit_payload = self._submit(model_id, body)
        request_id = self._extract_request_id(submit_payload)
        if not request_id:
            raise SemanticValidationError("Video provider did not return a request id.")

        status_url = self._extract_status_url(submit_payload, model_id=model_id, request_id=request_id)
        response_url = self._extract_response_url(submit_payload, model_id=model_id, request_id=request_id)
        terminal_status = self._poll_until_terminal(status_url)
        result_payload = self._get(response_url)
        self._raise_on_provider_error(result_payload)

        video = self._extract_video_reference(result_payload)
        if not video:
            raise SemanticValidationError("Video response did not contain a renderable video.")

        return {
            "request_id": request_id,
            "status": terminal_status,
            "status_url": status_url,
            "response_url": response_url,
            "videos": [video],
            "duration": int(duration),
        }

    def _perform_status(self, payload: dict[str, Any], *, model_id: str) -> JsonDict:
        request_id = str(payload.get("request_id", "") or "").strip()
        status_url = str(payload.get("status_url", "") or "").strip()
        response_url = str(payload.get("response_url", "") or "").strip()

        if not status_url:
            if not request_id:
                raise InputValidationError("Video request_id or status_url is required.")
            status_url = self._build_status_url(model_id, request_id)
        status_payload = self._get(with_query(status_url, logs=1))
        self._raise_on_provider_error(status_payload)
        status = self._extract_status(status_payload)

        videos: list[str] = []
        if status in {"completed", "succeeded", "ready", "done"}:
            request_id = request_id or self._extract_request_id(status_payload)
            if not response_url:
                if not request_id:
                    raise SemanticValidationError("Completed video status did not include a request id.")
                response_url = self._build_response_url(model_id, request_id)
            result_payload = self._get(response_url)
            self._raise_on_provider_error(result_payload)
            video = self._extract_video_reference(result_payload)
            if video:
                videos.append(video)

        return {
            "request_id": request_id,
            "status": status,
            "status_url": status_url,
            "response_url": response_url,
            "videos": videos,
        }

    def _submit(self, model_id: str, body: JsonDict) -> JsonDict:
        payload = self.transport.post_json(
            self._queue_url(model_id),
            body,
            headers=self._headers(),
            timeout_seconds=self.config.timeout_seconds,
        )
        self._raise_on_provider_error(payload)
        return payload

    def _poll_until_terminal(self, status_url: str) -> str:
        elapsed = 0.0
        while elapsed <= self.config.max_wait_seconds:
            payload = self._get(with_query(status_url, logs=1))
            self._raise_on_provider_error(payload)
            status = self._extract_status(payload)
            if status in {"completed", "succeeded", "ready", "done"}:
                return status
            if status in {"failed", "error", "cancelled", "canceled", "expired"}:
                message = extract_provider_error(payload) or f"Video generation ended with status '{status}'."
                raise APIExecutionError(message)
            self._sleeper(self.config.poll_interval_seconds)
            elapsed += self.config.poll_interval_seconds
        raise BoundaryExecutionError("Video generation timed out.")

    def _get(self, url: str) -> JsonDict:
        payload = self.transport.get_json(
            url,
            headers=self._headers(),
            timeout_seconds=self.config.timeout_seconds,
        )
        return payload

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Key {self.config.api_key}",
            "Content-Type": "application/json",
        }

    def _raise_on_provider_error(self, payload: JsonDict) -> None:
        provider_error = extract_provider_error(payload)
        if provider_error:
            raise APIExecutionError(provider_error)

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

    def _extract_status_url(self, payload: JsonDict, *, model_id: str, request_id: str) -> str:
        for key in ("status_url",):
            value = str(payload.get(key, "") or "").strip()
            if value:
                return value
        return self._build_status_url(model_id, request_id)

    def _extract_response_url(self, payload: JsonDict, *, model_id: str, request_id: str) -> str:
        for key in ("response_url", "result_url"):
            value = str(payload.get(key, "") or "").strip()
            if value:
                return value
        return self._build_response_url(model_id, request_id)

    def _extract_video_reference(self, payload: JsonDict) -> str:
        candidates: list[Any] = [
            payload,
            payload.get("data", {}),
            payload.get("result", {}),
            payload.get("output", {}),
            payload.get("video", {}),
        ]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            video_value = candidate.get("video")
            if isinstance(video_value, str) and video_value.strip():
                return video_value.strip()
            if isinstance(video_value, dict):
                url = str(video_value.get("url", "") or "").strip()
                if url:
                    return url
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
                        url = str(item.get("url", "") or "").strip()
                        if url:
                            return url
        return ""

    def _resolve_image_reference(self, payload: dict[str, Any]) -> str:
        for key in ("image", "image_url", "source_image", "image_path", "path"):
            if not self._has_value(payload, key):
                continue
            raw = str(payload[key]).strip()
            if raw.startswith("data:image/"):
                return raw
            parsed = urlparse(raw)
            if parsed.scheme in {"http", "https"}:
                return raw
            return normalize_image_reference(str(Path(raw)), source_label="Image source")
        raise InputValidationError("Video image input is required.")

    def _queue_url(self, model_id: str) -> str:
        return f"{self.config.queue_endpoint.rstrip('/')}/{model_id.lstrip('/')}"

    def _build_status_url(self, model_id: str, request_id: str) -> str:
        return f"{self._queue_url(model_id)}/requests/{request_id}/status"

    def _build_response_url(self, model_id: str, request_id: str) -> str:
        return f"{self._queue_url(model_id)}/requests/{request_id}"

    def _select_model_id(self, payload: dict[str, Any]) -> str:
        return self.config.image_to_video_model if self._has_image_input(payload) else self.config.text_to_video_model

    def _status_model_id(self, payload: dict[str, Any]) -> str:
        explicit = str(payload.get("model_id", "") or payload.get("model", "") or "").strip()
        if explicit:
            return explicit
        return self._select_model_id(payload)

    def _resolve_aspect_ratio(self, payload: dict[str, Any]) -> str:
        aspect_ratio = str(payload.get("aspect_ratio", "16:9") or "16:9").strip()
        if aspect_ratio not in {"16:9", "9:16"}:
            raise InputValidationError("Video aspect_ratio must be '16:9' or '9:16'.")
        return aspect_ratio

    def _resolve_resolution(self, payload: dict[str, Any]) -> str:
        resolution = str(payload.get("resolution", self.config.default_resolution) or self.config.default_resolution).strip().lower()
        if resolution not in {"480p", "580p", "720p"}:
            raise InputValidationError("Video resolution must be '480p', '580p', or '720p'.")
        return resolution

    def _resolve_num_frames(self, payload: dict[str, Any], *, duration: int) -> int:
        value = payload.get("num_frames")
        if value not in (None, ""):
            if not isinstance(value, int) or isinstance(value, bool) or int(value) not in {85, 129}:
                raise InputValidationError("Video num_frames must be 85 or 129.")
            return int(value)
        desired = max(1, int(round(duration * self.config.frames_per_second)))
        return 85 if desired <= 96 else 129

    def _optional_int(self, payload: dict[str, Any], key: str) -> int | None:
        value = payload.get(key)
        if value in (None, ""):
            return None
        if not isinstance(value, int) or isinstance(value, bool):
            raise InputValidationError(f"Video option '{key}' must be an integer.")
        return int(value)

    def _optional_bool(self, payload: dict[str, Any], key: str) -> bool | None:
        value = payload.get(key)
        if value is None:
            return None
        if not isinstance(value, bool):
            raise InputValidationError(f"Video option '{key}' must be a boolean.")
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
