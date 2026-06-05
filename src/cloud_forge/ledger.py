"""Append-only rail decision ledger (docs/proof/cloud-forge/rail-decisions.jsonl)."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
import threading
from pathlib import Path
from typing import Any
from uuid import uuid4


LEDGER_ID = "aais.cloud_forge.rail_decisions"
LEDGER_VERSION = "0.1"
SOURCE_CLASS = "routing_subsystem"
EVENT_TYPE = "rail_decision"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _default_ledger_path() -> Path:
    configured = os.getenv("CLOUD_FORGE_LEDGER_PATH")
    if configured:
        return Path(configured).expanduser()
    return (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "proof"
        / "cloud-forge"
        / "rail-decisions.jsonl"
    )


class RailDecisionLedger:
    """JSONL adapter for Cloud Forge rail decisions."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or _default_ledger_path())
        self._lock = threading.Lock()

    def append(
        self,
        cloud_forge_bundle: dict[str, Any],
        *,
        outcome_summary: str | None = None,
        outcome_class: str = "pending_review",
        tenant_id: str = "default",
    ) -> dict[str, Any]:
        decision = dict(cloud_forge_bundle.get("rail_decision") or {})
        plan = dict(cloud_forge_bundle.get("cognition_plan") or {})
        # Secondary checkpoint (defense-in-depth for Cloud Forge rail decisions):
        # Direct RailDecisionLedger().append bypasses schedule_request_observed / integration / log_ledger flag.
        # Require core decision data (task_id + rail) just like reward ledger guards on attribution + discovery_receipt_id.
        if not decision.get("task_id") or not decision.get("rail"):
            return {
                "status": "refused_by_checkpoint",
                "reason": "missing core rail_decision fields (task_id/rail) — possible direct ledger bypass of observed scheduling path",
            }
        record_id = f"rail-{uuid4().hex[:12]}"
        digest = sha256(
            _stable_json(
                {
                    "task_id": decision.get("task_id"),
                    "rail": decision.get("rail"),
                    "decided_at": decision.get("decided_at"),
                }
            ).encode("utf-8")
        ).hexdigest()[:16]

        record = {
            "record_id": record_id,
            "record_digest": digest,
            "timestamp": _utc_now_iso(),
            "ledger_id": LEDGER_ID,
            "ledger_version": LEDGER_VERSION,
            "source_class": SOURCE_CLASS,
            "event_type": EVENT_TYPE,
            "tenant_id": tenant_id,
            "outcome_class": outcome_class,
            "outcome_summary": (outcome_summary or "")[:500],
            "rail_decision": decision,
            "cognition_plan": plan,
            "task_snapshot": dict(cloud_forge_bundle.get("task_snapshot") or {}),
            "contract_version": cloud_forge_bundle.get("contract_version"),
        }

        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(_stable_json(record) + "\n")
        return record

    def read_records(self, *, limit: int = 200) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        return rows[-max(1, int(limit or 200)) :]

