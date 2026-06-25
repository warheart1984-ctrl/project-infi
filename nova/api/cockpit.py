"""Cockpit v2 HTTP routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from nova.crk.cockpit.summary_builder import build_cockpit_summary

router = APIRouter(prefix="/api/cockpit", tags=["cockpit"])


@router.get("/summary")
def cockpit_summary(epoch_id: str = "EPOCH:0:T0") -> dict[str, Any]:
    return build_cockpit_summary(epoch_id=epoch_id)
