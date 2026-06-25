"""HTTP orchestration for the Alpha governed core loop."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, EmailStr

from src.cori.pel.canonical import compute_loop_hash
from services.runtime.app.config import (
    ASSET_URL,
    AUDIT_URL,
    EVIDENCE_URL,
    IDENTITY_URL,
    VALIDATION_URL,
)


class CoreLoopError(Exception):
    pass


class CoreLoopRequest(BaseModel):
    email: EmailStr
    display_name: str
    asset: dict[str, Any]
    evidence: dict[str, Any]


async def _post_with_retry(
    client: httpx.AsyncClient,
    url: str,
    json: dict[str, Any],
    *,
    retries: int = 3,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = await client.post(url, json=json)
            if response.status_code == 200:
                body = response.json()
                if not isinstance(body, dict):
                    raise CoreLoopError(f"{url} returned non-object JSON")
                return body
            raise CoreLoopError(f"{url} returned {response.status_code}: {response.text}")
        except CoreLoopError:
            raise
        except Exception as exc:
            last_error = exc
            if attempt == retries - 1:
                break
    raise CoreLoopError(f"Failed POST {url}: {last_error}")


async def run_core_loop(
    payload: CoreLoopRequest | BaseModel,
    *,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """
    Executes the Alpha governed loop:
    1. Register/resolve subject
    2. Create asset
    3. Attach evidence
    4. Validate
    5. Emit audit record
    """
    if not isinstance(payload, CoreLoopRequest):
        payload = CoreLoopRequest.model_validate(payload.model_dump())

    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(timeout=5.0)

    assert client is not None
    try:
        subject = await _post_with_retry(
            client,
            f"{IDENTITY_URL}/register",
            {"email": str(payload.email), "display_name": payload.display_name},
        )
        subject_id = UUID(subject["subject_id"])

        asset = await _post_with_retry(
            client,
            f"{ASSET_URL}/assets",
            {"subject_id": str(subject_id), **payload.asset},
        )
        asset_id = UUID(asset["asset_id"])

        evidence = await _post_with_retry(
            client,
            f"{EVIDENCE_URL}/evidence",
            {"asset_id": str(asset_id), **payload.evidence},
        )
        evidence_id = UUID(evidence["evidence_id"])

        validation = await _post_with_retry(
            client,
            f"{VALIDATION_URL}/validations",
            {
                "asset_id": str(asset_id),
                "evidence_id": str(evidence_id),
                "evidence": payload.evidence,
            },
        )
        validation_id = UUID(validation["validation_id"])
        decision = str(validation["decision"])

        loop_hash = compute_loop_hash(
            subject_id=subject_id,
            asset_id=asset_id,
            evidence_id=evidence_id,
            validation_id=validation_id,
            decision=decision,
        )

        audit = await _post_with_retry(
            client,
            f"{AUDIT_URL}/audit",
            {
                "subject_id": str(subject_id),
                "asset_id": str(asset_id),
                "evidence_id": str(evidence_id),
                "validation_id": str(validation_id),
                "decision": decision,
                "loop_hash": loop_hash,
            },
        )
        audit_id = UUID(audit["audit_id"])

        return {
            "subject_id": subject_id,
            "asset_id": asset_id,
            "evidence_id": evidence_id,
            "validation_id": validation_id,
            "decision": decision,
            "audit_id": audit_id,
        }
    finally:
        if owns_client:
            await client.aclose()
