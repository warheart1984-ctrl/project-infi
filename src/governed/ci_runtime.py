"""Deterministic in-process runtime stubs for CI and local smoke tests."""

from __future__ import annotations

from typing import Any


class StubMissionRuntime:
    """Deterministic URG receipt when real URG would block governed CI seeds."""

    def run_mission(self, mission: dict[str, Any]) -> dict[str, Any]:
        mission_id = str(mission.get("mission_id") or "mission-ci-stub")
        return {
            "status": "ok",
            "mission_id": mission_id,
            "mission_receipt_schema": {"receipt_id": f"receipt-{mission_id}"},
            "urg_ingress": {"stamp_hash": f"stamp-{mission_id}"},
        }


def stub_mission_runtime() -> StubMissionRuntime:
    return StubMissionRuntime()
