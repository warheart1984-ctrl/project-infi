"""Temporal Replay service orchestration."""

# Mythic: Temporal Replay Machine
# Engineering: TemporalReplayMachineEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.temporal_replay.api_envelope import wrap_replay_payload
from src.temporal_replay.bundle import build_replay_bundle
from src.temporal_replay.compare import compare_runs
from src.temporal_replay.diff import build_reasoning_diff
from src.temporal_replay.forward import forward_replay
from src.temporal_replay.state import reconstruct_state
from src.temporal_replay.timeline import build_timeline
from src.temporal_replay.verify import verify_replay


class TemporalReplayService:
    def __init__(self, *, runtime_dir: Path | None = None):
        self.runtime_dir = runtime_dir

    def _receipt_for_mission(self, mission_id: str, tenant_id: str | None = None) -> dict[str, Any] | None:
        try:
            from src.ugr.mission.mission_receipt_store import MissionReceiptStore

            store = MissionReceiptStore(runtime_dir=self.runtime_dir, tenant_id=tenant_id)
            record = store.get_receipt(mission_id, tenant_id=store.tenant_id)
            if not record:
                return None
            return dict(record.get("mission_receipt_schema") or {})
        except Exception:
            return None

    def _workflow_run(self, run_id: str) -> dict[str, Any] | None:
        try:
            import app.db as workflow_db

            return workflow_db.get_workflow_run(run_id)
        except Exception:
            return None

    def timeline(
        self,
        subject_type: str,
        subject_id: str,
        *,
        tenant_id: str | None = None,
        workflow_run: dict[str, Any] | None = None,
        rebuild: bool = False,
    ) -> dict[str, Any]:
        if subject_type == "workflow_run" and workflow_run is None:
            workflow_run = self._workflow_run(subject_id)
        body = build_timeline(
            subject_type,
            subject_id,
            runtime_dir=self.runtime_dir,
            tenant_id=tenant_id,
            workflow_run=workflow_run,
            rebuild=rebuild,
        )
        body["summary"] = f"Timeline for {subject_type}/{subject_id}"
        return wrap_replay_payload(body, action_id="temporal_replay_timeline")

    def state_at(
        self,
        subject_type: str,
        subject_id: str,
        *,
        at: str | None = None,
        tenant_id: str | None = None,
        workflow_run: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if subject_type == "workflow_run" and workflow_run is None:
            workflow_run = self._workflow_run(subject_id)
        tl = build_timeline(
            subject_type,
            subject_id,
            runtime_dir=self.runtime_dir,
            tenant_id=tenant_id,
            workflow_run=workflow_run,
        )
        receipt = self._receipt_for_mission(subject_id, tenant_id) if subject_type == "mission" else None
        body = reconstruct_state(
            subject_type=subject_type,
            subject_id=subject_id,
            events=tl.get("events") or [],
            at=at,
            receipt_schema=receipt,
        )
        body["summary"] = f"State at {at or 'latest'}"
        return wrap_replay_payload(body, action_id="temporal_replay_state")

    def verify(
        self,
        subject_type: str,
        subject_id: str,
        *,
        at: str | None = None,
        tenant_id: str | None = None,
        workflow_run: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if subject_type == "workflow_run" and workflow_run is None:
            workflow_run = self._workflow_run(subject_id)
        tl = build_timeline(
            subject_type,
            subject_id,
            runtime_dir=self.runtime_dir,
            tenant_id=tenant_id,
            workflow_run=workflow_run,
        )
        body = verify_replay(
            subject_type=subject_type,
            subject_id=subject_id,
            events=tl.get("events") or [],
            at=at,
            tenant_id=tenant_id,
        )
        return wrap_replay_payload(body, action_id="temporal_replay_verify")

    def forward(
        self,
        subject_type: str,
        subject_id: str,
        *,
        fork_at: str,
        mode: str = "dry_run",
        steps: int = 1,
        target: str = "cloud_invariants",
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        tl = build_timeline(subject_type, subject_id, runtime_dir=self.runtime_dir, tenant_id=tenant_id)
        receipt = self._receipt_for_mission(subject_id, tenant_id) if subject_type == "mission" else None
        body = forward_replay(
            subject_type=subject_type,
            subject_id=subject_id,
            events=tl.get("events") or [],
            fork_at=fork_at,
            mode=mode,
            steps=steps,
            target=target,
            receipt_schema=receipt,
        )
        return wrap_replay_payload(body, action_id="temporal_replay_forward")

    def compare(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = compare_runs(
            dict(payload.get("left") or {}),
            dict(payload.get("right") or {}),
            align_by=str(payload.get("align_by") or "sequence"),
        )
        return wrap_replay_payload(body, action_id="temporal_replay_compare")

    def diff(
        self,
        subject_type: str,
        subject_id: str,
        *,
        fork_at: str,
        target: str = "cloud_invariants",
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        tl = build_timeline(subject_type, subject_id, runtime_dir=self.runtime_dir, tenant_id=tenant_id)
        receipt = self._receipt_for_mission(subject_id, tenant_id) if subject_type == "mission" else None
        body = build_reasoning_diff(
            subject_type=subject_type,
            subject_id=subject_id,
            events=tl.get("events") or [],
            fork_at=fork_at,
            target=target,
            receipt_schema=receipt,
        )
        return wrap_replay_payload(body, action_id="temporal_replay_diff")

    def bundle(
        self,
        subject_type: str,
        subject_id: str,
        *,
        fork_at: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        tl = build_timeline(subject_type, subject_id, runtime_dir=self.runtime_dir, tenant_id=tenant_id)
        receipt = self._receipt_for_mission(subject_id, tenant_id) if subject_type == "mission" else None
        body = build_replay_bundle(
            subject_type=subject_type,
            subject_id=subject_id,
            events=tl.get("events") or [],
            fork_at=fork_at,
            tenant_id=tenant_id,
            receipt_schema=receipt,
        )
        return wrap_replay_payload(body, action_id="temporal_replay_bundle")
