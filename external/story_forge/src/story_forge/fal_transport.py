from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib import error, parse, request

from story_forge.image_adapter.base_module import (
    APIExecutionError,
    BoundaryExecutionError,
    JsonDict,
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
            message = _extract_error_message(detail) or f"HTTP {exc.code}: {detail or exc.reason}"
            raise APIExecutionError(message) from exc
        except OSError as exc:
            raise APIExecutionError(str(exc)) from exc

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise BoundaryExecutionError("fal provider returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise BoundaryExecutionError("fal provider returned a non-object payload.")
        return payload


def with_query(url: str, **query: str | int | None) -> str:
    parsed = parse.urlparse(url)
    current = dict(parse.parse_qsl(parsed.query, keep_blank_values=True))
    for key, value in query.items():
        if value is None:
            continue
        current[key] = str(value)
    updated_query = parse.urlencode(current)
    return parse.urlunparse(parsed._replace(query=updated_query))


def extract_provider_error(payload: JsonDict) -> str:
    if isinstance(payload.get("error"), dict):
        error_payload = payload["error"]
        return str(error_payload.get("message", "") or error_payload)
    if payload.get("error"):
        return str(payload["error"])
    if isinstance(payload.get("detail"), list):
        parts: list[str] = []
        for item in payload["detail"]:
            if isinstance(item, dict):
                for key in ("msg", "message", "detail"):
                    value = str(item.get(key, "") or "").strip()
                    if value:
                        parts.append(value)
                        break
            elif item:
                parts.append(str(item))
        return "; ".join(part for part in parts if part).strip()
    if payload.get("detail"):
        return str(payload["detail"])
    return ""


def _extract_error_message(raw_body: str) -> str:
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        return raw_body.strip()
    if not isinstance(payload, dict):
        return raw_body.strip()
    return extract_provider_error(payload) or raw_body.strip()


__all__ = [
    "JsonTransport",
    "UrllibJsonTransport",
    "extract_provider_error",
    "with_query",
]
