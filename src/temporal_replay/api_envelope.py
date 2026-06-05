"""Stable Project Infi API envelope for replay routes."""

from __future__ import annotations

from typing import Any

from src.aais_ul import build_ul_snapshot
from src.aais_ul_substrate import attach_ul_substrate
from src.project_infi_law import PROJECT_INFI_CONTRACT_VERSION


def wrap_replay_payload(replay_body: dict[str, Any], *, action_id: str = "temporal_replay_read") -> dict[str, Any]:
    law_enforcement = {
        "contract_version": PROJECT_INFI_CONTRACT_VERSION,
        "source_of_truth": "project_infi_law",
        "execution_governance": {
            "authoritative_controller": "project_infi_law",
        },
        "replay": {
            "action_id": action_id,
            "runtime_effect": replay_body.get("runtime_effect") or "readout_only",
        },
    }
    ul_snapshot = build_ul_snapshot(
        ingress=[
            {
                "surface": "temporal_replay",
                "action_id": action_id,
                "subject": replay_body.get("subject") or replay_body.get("subject_id"),
            }
        ],
    )
    payload = {
        "replay": replay_body,
        "law_enforcement": law_enforcement,
        "ul_snapshot": ul_snapshot,
        "law_event_log": [
            {
                "action_id": action_id,
                "summary": replay_body.get("summary") or "Temporal replay readout",
                "timestamp": replay_body.get("at") or replay_body.get("fork_at"),
            }
        ],
    }
    return attach_ul_substrate(payload)
