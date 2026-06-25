"""Canonical models for the world continuity proof."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


class WorldEventRecord(BaseModel):
    id: str
    actor_id: str
    action_type: str
    action_payload: dict[str, Any] = Field(default_factory=dict)
    location: str
    timestamp: datetime


class WorldMemoryRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"WMR-{uuid4()}")
    event_id: str
    event_hash: str
    raw: dict[str, Any]
    observed_at: datetime = Field(default_factory=_utc_now)


class WorldState(BaseModel):
    locations: dict[str, dict[str, Any]] = Field(default_factory=dict)


class WorldClaim(BaseModel):
    id: str = Field(default_factory=lambda: f"WCLAIM-{uuid4()}")
    summary: str
    claim_type: str
    location: str


class WorldClaimRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"WCR-{uuid4()}")
    claim_id: str
    event_ids: list[str]
    raw: dict[str, Any]


class WorldVerificationRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"WVERIF-{uuid4()}")
    claim_id: str
    status: Literal["verified", "failed"]
    method: str = "verify_world_claim@alpha"
    details: dict[str, Any] = Field(default_factory=dict)
    verified_at: datetime = Field(default_factory=_utc_now)
