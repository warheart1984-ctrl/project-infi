"""FastAPI server for the Mechanic hosted pilot."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from mechanic.hosted.control_plane import HostedMechanicService
from mechanic.hosted.github_app import GitHubAppClient
from mechanic.hosted.security import hash_api_key, verify_api_key, verify_github_webhook_signature
from mechanic.hosted.settings import HostedSettings


class GitHubCallbackRequest(BaseModel):
    customer_id: str | None = None
    org: str | None = None
    repo_id: str
    installation_id: str | None = None
    default_branch: str = "main"
    permissions: list[str] = Field(default_factory=lambda: ["contents:read", "metadata:read"])


class CreateScanRequest(BaseModel):
    installation_id: str
    repo_path: str = ""
    scan_id: str | None = None
    case_id: str | None = None
    repo_ref: str | None = None
    trace_paths: list[str] = Field(default_factory=list)
    proof_tier: Literal["local", "ci", "second_machine"] = "local"
    max_repo_bytes: int = 25_000_000
    checkout: bool = False
    clone_url: str | None = None
    wait: bool = True
    timeout_seconds: int = 300


class TraceImportRequest(BaseModel):
    source: Literal["generic", "langsmith", "n8n", "make", "cursor"] = "generic"
    input_path: str
    output_path: str | None = None


class ReplayRequest(BaseModel):
    proof_tier: Literal["local", "ci", "second_machine"] = "ci"


def create_app(
    *,
    service: HostedMechanicService | None = None,
    artifact_root: str | Path | None = None,
    db_path: str | Path | None = None,
    api_key_hash: str | None = None,
    github_webhook_secret: str = "",
) -> FastAPI:
    settings = HostedSettings.from_env()
    resolved_service = service or HostedMechanicService(
        artifact_root=artifact_root or settings.artifact_root,
        db_path=db_path or settings.sqlite_path or None,
        database_url=settings.database_url,
        artifact_signing_secret=settings.artifact_signing_secret,
        max_workers=settings.max_workers,
        settings=settings,
    )
    expected_hash = api_key_hash or settings.api_key_hash
    webhook_secret = github_webhook_secret or settings.github_webhook_secret
    app = FastAPI(title="Mechanic Hosted Pilot", version="0.1.0")
    app.state.mechanic_service = resolved_service
    app.state.rate_limit: dict[str, list[float]] = {}

    @app.middleware("http")
    async def hardening_middleware(request: Request, call_next: Any) -> Any:
        content_length = int(request.headers.get("content-length") or 0)
        max_body = int(os.environ.get("MECHANIC_MAX_REQUEST_BYTES", "1048576"))
        if content_length > max_body:
            return JSONResponse({"detail": "request too large"}, status_code=413)
        key = request.headers.get("x-api-key") or request.client.host if request.client else "unknown"
        now = time.time()
        window = [stamp for stamp in app.state.rate_limit.get(key, []) if now - stamp < 60]
        if len(window) >= int(os.environ.get("MECHANIC_RATE_LIMIT_PER_MINUTE", "120")):
            return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
        window.append(now)
        app.state.rate_limit[key] = window
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    def require_api_key(x_api_key: str = Header(default="")) -> None:
        if (expected_hash or settings.require_api_key) and not verify_api_key(provided=x_api_key, expected_hash=expected_hash):
            raise HTTPException(status_code=401, detail="invalid api key")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"ok": "true", "service": "mechanic-hosted"}

    @app.get("/readyz")
    def readyz() -> dict[str, Any]:
        return {"ok": True, "deploy_missing": settings.validate_for_deploy()}

    @app.post("/v1/installations/github/callback", dependencies=[Depends(require_api_key)])
    async def github_callback(
        request: Request,
        x_hub_signature_256: str = Header(default=""),
    ) -> dict[str, Any]:
        body = await request.body()
        if webhook_secret and not verify_github_webhook_signature(
            body=body,
            signature_header=x_hub_signature_256,
            webhook_secret=webhook_secret,
        ):
            raise HTTPException(status_code=401, detail="invalid github webhook signature")
        payload = json.loads(body.decode("utf-8") or "{}")
        if "repository" in payload or "installation" in payload:
            payload = GitHubAppClient.installation_payload_from_webhook(payload)
        else:
            payload = GitHubCallbackRequest.model_validate(payload).model_dump()
        try:
            return resolved_service.github_installation_callback(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/v1/scans", dependencies=[Depends(require_api_key)])
    def create_scan(payload: CreateScanRequest) -> dict[str, Any]:
        try:
            return resolved_service.create_scan(payload.model_dump(exclude_none=True))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/v1/scans/{scan_id}", dependencies=[Depends(require_api_key)])
    def get_scan(scan_id: str) -> dict[str, Any]:
        try:
            return resolved_service.get_scan(scan_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/v1/scans/{scan_id}/report", dependencies=[Depends(require_api_key)])
    def get_report(scan_id: str) -> dict[str, Any]:
        try:
            return resolved_service.get_scan_report(scan_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/v1/scans/{scan_id}/artifacts", dependencies=[Depends(require_api_key)])
    def get_artifacts(scan_id: str) -> dict[str, Any]:
        try:
            return resolved_service.get_scan_artifacts(scan_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/v1/traces/import", dependencies=[Depends(require_api_key)])
    def import_trace(payload: TraceImportRequest) -> dict[str, Any]:
        try:
            return resolved_service.import_trace(payload.model_dump(exclude_none=True))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/v1/scans/{scan_id}/replay", dependencies=[Depends(require_api_key)])
    def replay(scan_id: str, payload: ReplayRequest) -> dict[str, Any]:
        try:
            return resolved_service.replay_scan(scan_id, proof_tier=payload.proof_tier)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return app


app = create_app()
