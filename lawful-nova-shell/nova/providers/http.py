from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Iterator

from nova.errors import ProviderError


def post_json(
    url: str,
    payload: dict[str, Any],
    *,
    timeout: float,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise ProviderError(code="PROVIDER_HTTP_ERROR", message=f"{exc.code}: {exc.read().decode('utf-8')[:256]}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(code="PROVIDER_REQUEST_FAILED", message=str(exc)) from exc
    if status != 200:
        raise ProviderError(code="PROVIDER_HTTP_ERROR", message=f"{status}: {body[:256]}")
    return json.loads(body or "{}")


def post_json_lines(url: str, payload: dict[str, Any], *, timeout: float) -> Iterator[bytes]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            for line in response:
                cleaned = line.strip()
                if cleaned:
                    yield cleaned
    except urllib.error.HTTPError as exc:
        raise ProviderError(code="PROVIDER_STREAM_HTTP_ERROR", message=f"{exc.code}: {exc.read().decode('utf-8')[:256]}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(code="PROVIDER_STREAM_REQUEST_FAILED", message=str(exc)) from exc
