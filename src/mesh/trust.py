"""Peer trust scoring from handshake and gossip outcomes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.mesh.paths import mesh_dir

TRUST_FILENAME = "trust_scores.json"

DEFAULT_SCORE = 0.5
ALPHA = 0.2


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def trust_path(base_dir: str | Path | None = None) -> Path:
    return mesh_dir(base_dir) / TRUST_FILENAME


class TrustStore:
    def __init__(self, base_dir: str | Path | None = None):
        self.path = trust_path(base_dir)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({})

    def _read(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def score(self, peer_node_id: str) -> float:
        return float(self._read().get(peer_node_id, {}).get("score", DEFAULT_SCORE))

    def record(self, peer_node_id: str, event: str, *, delta_hint: float | None = None) -> float:
        hints = {
            "handshake_ok": 0.85,
            "handshake_fail": 0.1,
            "ledger_agree": 0.9,
            "ledger_diverge": 0.4,
            "gossip_ok": 0.75,
            "gossip_fail": 0.2,
            "admit_consistent": 0.8,
            "reject_consistent": 0.7,
            "evaluate_admit": 0.8,
            "evaluate_reject": 0.65,
        }
        target = delta_hint if delta_hint is not None else hints.get(event, 0.5)

        data = self._read()
        prev = float(data.get(peer_node_id, {}).get("score", DEFAULT_SCORE))
        new_score = (1 - ALPHA) * prev + ALPHA * target
        new_score = max(0.0, min(1.0, new_score))

        data[peer_node_id] = {
            "score": round(new_score, 4),
            "last_event": event,
            "updated_at": _utc_now(),
        }
        self._write(data)
        return new_score

    def penalty_for_peer(self, peer_node_id: str) -> float:
        data = self._read()
        if peer_node_id not in data:
            return 0.15
        score = float(data[peer_node_id].get("score", DEFAULT_SCORE))
        if score >= 0.8:
            return 0.0
        if score >= 0.5:
            return 0.05
        return 0.15

    def snapshot(self) -> dict:
        return self._read()
