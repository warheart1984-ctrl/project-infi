"""HTTP client for the isolated ForgeEval evaluator service."""

from __future__ import annotations

import os
from typing import Any
import uuid

import requests

from forge_eval.schemas import EvaluationErrorResponse, EvaluationRequest, EvaluationSuccessResponse


VALID_MODES = {"io_tests", "llm_rubric", "repo_patch"}


def normalize_forge_eval_response(payload: Any) -> dict[str, Any] | None:
    """Validate the evaluator response envelope."""

    if not isinstance(payload, dict):
        return None
    try:
        return EvaluationSuccessResponse.model_validate(payload).model_dump(exclude_none=True)
    except ValueError:
        pass
    try:
        return EvaluationErrorResponse.model_validate(payload).model_dump(exclude_none=True)
    except ValueError:
        return None


class ForgeEvalClient:
    """AAIS-side client for the evaluator service."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        session: requests.sessions.Session | Any | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (
            str(base_url or os.getenv("FORGE_EVAL_BASE_URL") or "http://127.0.0.1:6061").rstrip("/")
        )
        self.timeout_seconds = float(
            timeout_seconds
            if timeout_seconds is not None
            else os.getenv("FORGE_EVAL_CLIENT_TIMEOUT_SECONDS", "30")
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
            raise RuntimeError(f"ForgeEval unavailable: {exc}") from exc

    def evaluate(
        self,
        *,
        mode: str,
        payload: dict[str, Any],
        task_id: str | None = None,
    ) -> dict[str, Any]:
        normalized_mode = str(mode or "").strip()
        if normalized_mode not in VALID_MODES:
            raise ValueError(f"Unsupported ForgeEval mode: {mode}")

        body = EvaluationRequest.model_validate(
            {
                "task_id": str(task_id or f"forge-eval-{uuid.uuid4().hex[:12]}"),
                "mode": normalized_mode,
                "payload": dict(payload or {}),
            }
        ).model_dump(exclude_none=True)

        try:
            response = self.session.post(
                f"{self.base_url}/evaluate",
                json=body,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"ForgeEval unavailable: {exc}") from exc

        try:
            normalized = normalize_forge_eval_response(response.json())
        except ValueError as exc:
            raise RuntimeError("ForgeEval returned invalid JSON.") from exc

        if normalized is None:
            raise RuntimeError("ForgeEval returned an invalid response contract.")
        from src.aais_ul.runtime import wrap_contractor_payload

        return wrap_contractor_payload(normalized)


forge_eval_client = ForgeEvalClient()
