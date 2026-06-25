"""HTTP client for the isolated EvolveEngine service."""

from __future__ import annotations

import os
from typing import Any
import uuid

import requests

from evolve_engine.schemas import EvolutionErrorResponse, EvolutionRequest, EvolutionSuccessResponse


VALID_EVALUATION_MODES = {"forge_eval"}


def normalize_evolve_response(payload: Any) -> dict[str, Any] | None:
    """Validate the evolve response envelope."""

    if not isinstance(payload, dict):
        return None
    try:
        return EvolutionSuccessResponse.model_validate(payload).model_dump(exclude_none=True)
    except ValueError:
        pass
    try:
        return EvolutionErrorResponse.model_validate(payload).model_dump(exclude_none=True)
    except ValueError:
        return None


class EvolveClient:
    """AAIS-side client for the EvolveEngine service."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        session: requests.sessions.Session | Any | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = str(base_url or os.getenv("EVOLVE_BASE_URL") or "http://127.0.0.1:6062").rstrip("/")
        self.timeout_seconds = float(
            timeout_seconds
            if timeout_seconds is not None
            else os.getenv("EVOLVE_CLIENT_TIMEOUT_SECONDS", "60")
        )
        self.session = session or requests.Session()

    def health(self) -> dict[str, Any]:
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout_seconds,
            )
            if getattr(response, "status_code", 200) >= 400:
                raise RuntimeError(response.text or response.status_code)
            return dict(response.json() or {})
        except requests.RequestException as exc:
            raise RuntimeError(f"EvolveEngine unavailable: {exc}") from exc

    def evolve(
        self,
        *,
        task: str,
        config: dict[str, Any] | None = None,
        evaluation: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
        job_id: str | None = None,
        jarvis_run_id: str | None = None,
    ) -> dict[str, Any]:
        body = EvolutionRequest.model_validate(
            {
                "job_id": str(job_id or f"evolve-{uuid.uuid4().hex[:12]}"),
                "task": str(task or "").strip(),
                "config": dict(config or {}),
                "evaluation": dict(evaluation or {}),
                "constraints": dict(constraints or {}),
                "jarvis_run_id": jarvis_run_id,
            }
        ).model_dump(exclude_none=True)

        try:
            response = self.session.post(
                f"{self.base_url}/evolve",
                json=body,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"EvolveEngine unavailable: {exc}") from exc

        try:
            normalized = normalize_evolve_response(response.json())
        except ValueError as exc:
            raise RuntimeError("EvolveEngine returned invalid JSON.") from exc

        if normalized is None:
            raise RuntimeError("EvolveEngine returned an invalid response contract.")
        from src.aais_ul.runtime import wrap_runtime_snapshot

        return wrap_runtime_snapshot(normalized)

    def get_job_trace(self, job_id: str) -> dict[str, Any]:
        return self._get_json(f"/traces/jobs/{job_id}")

    def get_job_evaluations(self, job_id: str, *, limit: int = 200) -> dict[str, Any]:
        return self._get_json(f"/traces/jobs/{job_id}/evaluations?limit={max(1, int(limit))}")

    def get_run_trace(self, jarvis_run_id: str) -> dict[str, Any]:
        return self._get_json(f"/traces/runs/{jarvis_run_id}")

    def list_hall_of_fame(self, *, limit: int = 20) -> dict[str, Any]:
        return self._get_json(f"/traces/hall-of-fame?limit={max(1, int(limit))}")

    def list_hall_of_shame(self, *, limit: int = 20) -> dict[str, Any]:
        return self._get_json(f"/traces/hall-of-shame?limit={max(1, int(limit))}")

    def prune_retention(
        self,
        *,
        max_jobs: int | None = None,
        max_hall_entries: int | None = None,
        max_evaluations: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if max_jobs is not None:
            body["max_jobs"] = int(max_jobs)
        if max_hall_entries is not None:
            body["max_hall_entries"] = int(max_hall_entries)
        if max_evaluations is not None:
            body["max_evaluations"] = int(max_evaluations)
        try:
            response = self.session.post(
                f"{self.base_url}/maintenance/prune",
                json=body,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"EvolveEngine unavailable: {exc}") from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError("EvolveEngine returned invalid JSON.") from exc
        if getattr(response, "status_code", 200) >= 400:
            raise RuntimeError(str((payload or {}).get("error") or response.text or response.status_code))
        return dict(payload or {})

    def _get_json(self, path: str) -> dict[str, Any]:
        try:
            response = self.session.get(
                f"{self.base_url}{path}",
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"EvolveEngine unavailable: {exc}") from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError("EvolveEngine returned invalid JSON.") from exc
        if getattr(response, "status_code", 200) >= 400:
            message = str((payload or {}).get("error") or response.text or response.status_code)
            if getattr(response, "status_code", 200) == 404:
                raise FileNotFoundError(message)
            raise RuntimeError(message)
        return dict(payload or {})


evolve_client = EvolveClient()
