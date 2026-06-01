from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import os
import time
import urllib.request

from aais.launcher import main


LEGACY_BACKEND_PORT = 5000
CANONICAL_BACKEND_PORT = 8000
LEGACY_BACKEND_URL = f"http://127.0.0.1:{LEGACY_BACKEND_PORT}"
LEGACY_BACKEND_HEALTH_URL = f"{LEGACY_BACKEND_URL}/health"
CANONICAL_BACKEND_URL = f"http://127.0.0.1:{CANONICAL_BACKEND_PORT}"
CANONICAL_BACKEND_HEALTH_URL = f"{CANONICAL_BACKEND_URL}/health"
BACKEND_TIMEOUT_SECONDS = 45


def build_frontend_env(backend_url: str, base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(base_env or os.environ.copy())
    env["VITE_API_URL"] = str(backend_url)
    env["REACT_APP_API_URL"] = str(backend_url)
    return env


def http_ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return 200 <= response.status < 500
    except Exception:
        return False


def resolve_existing_backend(kind: str | None = None) -> dict[str, str] | None:
    targets = [
        {
            "backend_kind": "canonical",
            "backend_mode": "canonical",
            "backend_runtime": "already_running",
            "backend_url": CANONICAL_BACKEND_URL,
            "health_url": CANONICAL_BACKEND_HEALTH_URL,
        },
        {
            "backend_kind": "legacy",
            "backend_mode": "legacy",
            "backend_runtime": "already_running",
            "backend_url": LEGACY_BACKEND_URL,
            "health_url": LEGACY_BACKEND_HEALTH_URL,
        },
    ]

    for target in targets:
        if kind and target["backend_kind"] != kind:
            continue
        if http_ready(target["health_url"]):
            return {
                "status": "existing",
                "backend_kind": target["backend_kind"],
                "backend_mode": target["backend_mode"],
                "backend_runtime": target["backend_runtime"],
                "backend_url": target["backend_url"],
            }

    return None


def build_backend_candidates() -> list[dict[str, str]]:
    return [
        {
            "label": "AAIS canonical runtime",
            "kind": "canonical",
            "mode": "canonical",
            "backend_url": CANONICAL_BACKEND_URL,
            "health_url": CANONICAL_BACKEND_HEALTH_URL,
        }
    ]


def start_backend_candidate(
    candidate: dict[str, str],
    *,
    failures: list[str] | None = None,
) -> dict[str, str] | None:
    deadline = time.time() + BACKEND_TIMEOUT_SECONDS
    while time.time() < deadline:
        if http_ready(candidate["health_url"]):
            return {
                "status": "started",
                "backend_kind": candidate["kind"],
                "backend_mode": candidate["mode"],
                "backend_runtime": candidate["label"],
                "backend_url": candidate["backend_url"],
            }
        time.sleep(1)

    if failures is not None:
        failures.append(f"{candidate['label']} did not become healthy within {BACKEND_TIMEOUT_SECONDS}s.")
    return None


def ensure_backend() -> dict[str, str]:
    existing_canonical = resolve_existing_backend(kind="canonical")
    if existing_canonical:
        return existing_canonical

    existing_legacy = resolve_existing_backend(kind="legacy")
    candidates = build_backend_candidates()
    canonical_candidate = next(
        (candidate for candidate in candidates if candidate.get("kind") == "canonical"),
        None,
    )

    if existing_legacy and canonical_candidate:
        promoted_backend = start_backend_candidate(canonical_candidate)
        if promoted_backend:
            return promoted_backend
        return existing_legacy

    if existing_legacy:
        return existing_legacy

    failures: list[str] = []
    for candidate in candidates:
        backend_state = start_backend_candidate(candidate, failures=failures)
        if backend_state:
            return backend_state

    raise RuntimeError("Jarvis backend could not be started.\n\n" + "\n".join(failures))


if __name__ == "__main__":
    raise SystemExit(main())
