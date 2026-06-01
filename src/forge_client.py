"""HTTP client for the isolated Forge contractor service."""

from __future__ import annotations

import os
from typing import Any
import uuid

import requests

from forge.schemas import ContractorErrorResponse, ContractorRequest, ContractorSuccessResponse


VALID_KINDS = {"generate_code", "generate_diff", "generate_tests", "analyze", "repo_manager"}


def normalize_forge_response(payload: Any) -> dict[str, Any] | None:
    """Validate the contractor response without sharing service internals."""

    if not isinstance(payload, dict):
        return None
    try:
        return ContractorSuccessResponse.model_validate(payload).model_dump(exclude_none=True)
    except ValueError:
        pass
    try:
        return ContractorErrorResponse.model_validate(payload).model_dump(exclude_none=True)
    except ValueError:
        return None


def auto_approve_forge_result(result: dict[str, Any] | None) -> bool:
    """Forge v1 contractor responses always remain review-gated inside AAIS."""

    return False


def _legacy_context_to_contract(task: str, context: dict[str, Any]) -> dict[str, Any]:
    constraints: dict[str, Any] = {}
    if context.get("language"):
        constraints["language"] = context.get("language")
    if context.get("constraints"):
        constraints["requirements"] = list(context.get("constraints") or [])
    if context.get("style"):
        constraints["style"] = dict(context.get("style") or {})
    if context.get("max_output_chars"):
        constraints["max_output_chars"] = context.get("max_output_chars")
    return {
        "files": list(context.get("files") or []),
        "goal": " ".join(str(task or "").split()).strip(),
        "constraints": constraints,
    }


class ForgeClient:
    """Small AAIS-side client that talks to Forge only through HTTP."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        session: requests.sessions.Session | Any | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (
            str(base_url or os.getenv("FORGE_BASE_URL") or "http://127.0.0.1:6060").rstrip("/")
        )
        self.timeout_seconds = float(
            timeout_seconds
            if timeout_seconds is not None
            else os.getenv("FORGE_CLIENT_TIMEOUT_SECONDS", "30")
        )
        self.session = session or requests.Session()

    def health(self) -> dict[str, Any]:
        """Fetch service health from the isolated Forge process."""

        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout_seconds,
            )
            if getattr(response, "status_code", 200) >= 400:
                detail = None
                try:
                    detail = (response.json() or {}).get("detail")
                except ValueError:
                    detail = getattr(response, "text", "")
                raise RuntimeError(
                    f"Forge contractor unavailable: {detail or getattr(response, 'text', '') or response.status_code}"
                )
            return dict(response.json() or {})
        except requests.RequestException as exc:
            raise RuntimeError(f"Forge contractor unavailable: {exc}") from exc

    def request(
        self,
        *,
        kind: str,
        context: dict[str, Any],
        task_id: str | None = None,
    ) -> dict[str, Any]:
        """Send one contractor request to the isolated Forge service."""

        normalized_kind = str(kind or "").strip()
        if normalized_kind not in VALID_KINDS:
            raise ValueError(f"Unsupported Forge kind: {kind}")

        payload = ContractorRequest.model_validate(
            {
                "task_id": str(task_id or f"forge-{uuid.uuid4().hex[:12]}"),
                "kind": normalized_kind,
                "context": dict(context or {}),
            }
        ).model_dump(exclude_none=True)

        try:
            response = self.session.post(
                f"{self.base_url}/contractor",
                json=payload,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"Forge contractor unavailable: {exc}") from exc

        try:
            normalized = normalize_forge_response(response.json())
        except ValueError as exc:
            raise RuntimeError("Forge contractor returned invalid JSON.") from exc

        if normalized is None:
            raise RuntimeError("Forge contractor returned an invalid response contract.")
        from src.aais_ul_substrate import wrap_contractor_payload

        return wrap_contractor_payload(normalized)

    def run_code_task(
        self,
        task: str,
        context: dict[str, Any],
        *,
        kind: str = "generate_diff",
    ) -> dict[str, Any]:
        """Compatibility wrapper that maps the legacy Forge call to the contractor contract."""

        return self.request(
            kind=kind,
            context=_legacy_context_to_contract(task, dict(context or {})),
        )


forge_client = ForgeClient()
