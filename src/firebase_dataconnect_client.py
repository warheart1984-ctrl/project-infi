"""Firebase Data Connect REST client for Memory Board vector projection.

Uses connector predefined operations (executeQuery / executeMutation) with a
service account in production, or the Data Connect emulator when
DATA_CONNECT_EMULATOR_HOST is set.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_LOCATION = "us-central1"
DEFAULT_SERVICE = "jarvis-memory"
DEFAULT_CONNECTOR = "jarvis-memory-connector"
PRODUCTION_BASE = "https://firebasedataconnect.googleapis.com"


def firebase_configured() -> bool:
    return bool(os.getenv("FIREBASE_PROJECT_ID", "").strip())


def _project_id() -> str:
    project = os.getenv("FIREBASE_PROJECT_ID", "").strip()
    if not project:
        raise RuntimeError("FIREBASE_PROJECT_ID is required for Firebase Data Connect.")
    return project


def _location() -> str:
    return os.getenv("FIREBASE_DATA_CONNECT_LOCATION", DEFAULT_LOCATION).strip() or DEFAULT_LOCATION


def _service_id() -> str:
    return os.getenv("FIREBASE_DATA_CONNECT_SERVICE", DEFAULT_SERVICE).strip() or DEFAULT_SERVICE


def _connector_id() -> str:
    return (
        os.getenv("FIREBASE_DATA_CONNECT_CONNECTOR", DEFAULT_CONNECTOR).strip()
        or DEFAULT_CONNECTOR
    )


def _connector_resource() -> str:
    return (
        f"projects/{_project_id()}/locations/{_location()}/services/{_service_id()}"
        f"/connectors/{_connector_id()}"
    )


def _api_root() -> str:
    emulator = os.getenv("DATA_CONNECT_EMULATOR_HOST", "").strip()
    if emulator:
        if emulator.startswith("http://") or emulator.startswith("https://"):
            return emulator.rstrip("/")
        return f"http://{emulator}"
    return PRODUCTION_BASE


def _auth_headers() -> dict[str, str]:
    if os.getenv("DATA_CONNECT_EMULATOR_HOST", "").strip():
        return {"Content-Type": "application/json"}
    token = _access_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _access_token() -> str:
    try:
        import google.auth
        import google.auth.transport.requests
    except ImportError as exc:
        raise RuntimeError(
            "google-auth is required for Firebase Data Connect (see requirements-advanced.txt)."
        ) from exc

    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(google.auth.transport.requests.Request())
    if not credentials.token:
        raise RuntimeError("Failed to obtain Google access token for Firebase Data Connect.")
    return credentials.token


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=_auth_headers(), method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Firebase Data Connect HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Firebase Data Connect request failed: {exc}") from exc

    parsed = json.loads(raw) if raw else {}
    if not isinstance(parsed, dict):
        raise RuntimeError("Firebase Data Connect returned a non-object JSON payload.")
    errors = parsed.get("errors")
    if errors:
        raise RuntimeError(f"Firebase Data Connect GraphQL errors: {errors}")
    return parsed


def execute_query(operation_name: str, variables: dict[str, Any]) -> dict[str, Any]:
    url = f"{_api_root()}/v1/{_connector_resource()}:executeQuery"
    return _post_json(
        url,
        {
            "operationName": operation_name,
            "variables": variables,
        },
    )


def execute_mutation(operation_name: str, variables: dict[str, Any]) -> dict[str, Any]:
    url = f"{_api_root()}/v1/{_connector_resource()}:executeMutation"
    return _post_json(
        url,
        {
            "operationName": operation_name,
            "variables": variables,
        },
    )


def rows_from_query(payload: dict[str, Any], field: str) -> list[dict[str, Any]]:
    data = payload.get("data")
    if not isinstance(data, dict):
        return []
    rows = data.get(field)
    if rows is None:
        return []
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    if isinstance(rows, dict):
        return [rows]
    return []
