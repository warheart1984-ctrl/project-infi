"""CORI Alpha — governed evidence factory."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from nova.bridges import panel_store

from src.continuity.continuity_store import ContinuityStore, get_continuity_store
from src.cori.asset_registry import AssetRegistry, get_asset_registry


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def hash_evidence_payload(payload: dict[str, Any]) -> str:
    """Deterministic SHA-256 over canonical JSON."""
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class EvidenceEnvelope:
    """Structured, hashable, chainable evidence record."""

    evidence_class: str
    event_type: str
    payload: dict[str, Any]
    steward_identity: str | None = None
    asset_id: str | None = None
    law_eval_id: str | None = None
    mission_id: str | None = None
    execution_id: str | None = None
    nexus_event_id: str | None = None
    introduced_by: str | None = None
    evidence_id: str = field(default_factory=lambda: f"ev-{uuid4().hex[:16]}")
    recorded_at: str = field(default_factory=_now)
    payload_hash: str = ""

    def __post_init__(self) -> None:
        if not self.payload_hash:
            self.payload_hash = hash_evidence_payload(self.payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_class": self.evidence_class,
            "event_type": self.event_type,
            "payload": self.payload,
            "payload_hash": self.payload_hash,
            "recorded_at": self.recorded_at,
            "steward_identity": self.steward_identity,
            "asset_id": self.asset_id,
            "law_eval_id": self.law_eval_id,
            "mission_id": self.mission_id,
            "execution_id": self.execution_id,
            "nexus_event_id": self.nexus_event_id,
            "introduced_by": self.introduced_by,
        }


class EvidenceFactory:
    """
    Write-through evidence emitter for CORI Alpha.

    Every meaningful runtime event becomes structured, queryable continuity evidence.
    """

    def __init__(
        self,
        *,
        continuity: ContinuityStore | None = None,
        assets: AssetRegistry | None = None,
    ) -> None:
        self._continuity = continuity or get_continuity_store()
        self._assets = assets or get_asset_registry(store=self._continuity)

    def emit(self, envelope: EvidenceEnvelope) -> int:
        """Write evidence to continuity_events (write-through on emit)."""
        return self._continuity.record_event(envelope.event_type, envelope.to_dict())

    def emit_identity_snapshot(
        self,
        steward_identity: str,
        snapshot: dict[str, Any],
        *,
        event_type: str = "identity_snapshot",
    ) -> EvidenceEnvelope:
        envelope = EvidenceEnvelope(
            evidence_class="identity",
            event_type=event_type,
            payload=snapshot,
            steward_identity=steward_identity,
        )
        self._continuity.record_identity_snapshot(steward_identity, snapshot)
        self.emit(envelope)
        return envelope

    def emit_asset_created(
        self,
        asset_id: str,
        metadata: dict[str, Any],
        *,
        steward_identity: str | None = None,
        law_eval_id: str | None = None,
    ) -> EvidenceEnvelope:
        self._assets.register(asset_id, metadata, steward_identity=steward_identity)
        envelope = EvidenceEnvelope(
            evidence_class="asset",
            event_type="asset_created",
            payload={"asset_id": asset_id, **metadata},
            steward_identity=steward_identity,
            asset_id=asset_id,
            law_eval_id=law_eval_id,
        )
        self.emit(envelope)
        return envelope

    def emit_evidence_attached(
        self,
        *,
        asset_id: str,
        artifact: dict[str, Any],
        steward_identity: str | None = None,
        law_eval_id: str | None = None,
        mission_id: str | None = None,
    ) -> EvidenceEnvelope:
        body = dict(artifact)
        body["asset_id"] = asset_id
        envelope = EvidenceEnvelope(
            evidence_class="evidence",
            event_type="evidence_attached",
            payload=body,
            steward_identity=steward_identity,
            asset_id=asset_id,
            law_eval_id=law_eval_id,
            mission_id=mission_id,
        )
        self.emit(envelope)
        hashed = EvidenceEnvelope(
            evidence_class="evidence",
            event_type="evidence_hashed",
            payload={
                "parent_evidence_id": envelope.evidence_id,
                "payload_hash": envelope.payload_hash,
                "asset_id": asset_id,
            },
            steward_identity=steward_identity,
            asset_id=asset_id,
            law_eval_id=law_eval_id,
            mission_id=mission_id,
        )
        self.emit(hashed)
        return envelope

    def emit_validation(
        self,
        *,
        asset_id: str,
        law_eval_id: str,
        decision: str,
        steward_identity: str | None = None,
        mission_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> tuple[EvidenceEnvelope, EvidenceEnvelope]:
        requested = EvidenceEnvelope(
            evidence_class="validation",
            event_type="validation_requested",
            payload={
                "asset_id": asset_id,
                "law_eval_id": law_eval_id,
                "mission_id": mission_id,
            },
            steward_identity=steward_identity,
            asset_id=asset_id,
            law_eval_id=law_eval_id,
            mission_id=mission_id,
        )
        self.emit(requested)
        decided = EvidenceEnvelope(
            evidence_class="validation",
            event_type="validation_decided",
            payload={
                "asset_id": asset_id,
                "law_eval_id": law_eval_id,
                "mission_id": mission_id,
                "decision": decision,
                "request_evidence_id": requested.evidence_id,
                **(details or {}),
            },
            steward_identity=steward_identity,
            asset_id=asset_id,
            law_eval_id=law_eval_id,
            mission_id=mission_id,
        )
        self.emit(decided)
        return requested, decided

    def emit_law_eval(
        self,
        law_eval: dict[str, Any],
        *,
        steward_identity: str | None = None,
        asset_id: str | None = None,
        introduced_by: str | None = "nova",
    ) -> EvidenceEnvelope:
        envelope = EvidenceEnvelope(
            evidence_class="validation",
            event_type="law_eval",
            payload=law_eval,
            steward_identity=steward_identity,
            asset_id=asset_id,
            law_eval_id=str(law_eval.get("id") or ""),
            introduced_by=introduced_by,
        )
        self.emit(envelope)
        return envelope

    def emit_urg_mission(
        self,
        urg_receipt: dict[str, Any],
        *,
        steward_identity: str | None = None,
        law_eval_id: str | None = None,
        asset_id: str | None = None,
        governed: bool = True,
    ) -> EvidenceEnvelope:
        body = dict(urg_receipt)
        body["governed"] = governed
        envelope = EvidenceEnvelope(
            evidence_class="validation",
            event_type="urg_mission",
            payload=body,
            steward_identity=steward_identity,
            asset_id=asset_id,
            law_eval_id=law_eval_id,
            mission_id=str(urg_receipt.get("mission_id") or ""),
        )
        self.emit(envelope)
        return envelope

    def emit_aaes_exec(
        self,
        aaes_receipt: dict[str, Any],
        *,
        steward_identity: str | None = None,
        law_eval_id: str | None = None,
        mission_id: str | None = None,
        asset_id: str | None = None,
    ) -> EvidenceEnvelope:
        envelope = EvidenceEnvelope(
            evidence_class="execution",
            event_type="aaes_exec",
            payload=aaes_receipt,
            steward_identity=steward_identity,
            asset_id=asset_id,
            law_eval_id=law_eval_id,
            mission_id=mission_id,
            execution_id=str(
                aaes_receipt.get("execution_id") or aaes_receipt.get("trace_id") or ""
            ),
        )
        self.emit(envelope)
        return envelope

    def emit_nexus_event(
        self,
        nexus_event: dict[str, Any],
        *,
        steward_identity: str | None = None,
        law_eval_id: str | None = None,
        mission_id: str | None = None,
        execution_id: str | None = None,
        asset_id: str | None = None,
    ) -> EvidenceEnvelope:
        envelope = EvidenceEnvelope(
            evidence_class="execution",
            event_type="nexus_event",
            payload=nexus_event,
            steward_identity=steward_identity,
            asset_id=asset_id,
            law_eval_id=law_eval_id,
            mission_id=mission_id,
            execution_id=execution_id,
            nexus_event_id=str(nexus_event.get("event_id") or nexus_event.get("recorded_at") or ""),
        )
        self.emit(envelope)
        return envelope

    def emit_panel(
        self,
        panel_type: str,
        panel_payload: dict[str, Any],
        *,
        steward_identity: str | None = None,
        law_eval_id: str | None = None,
        mission_id: str | None = None,
        execution_id: str | None = None,
    ) -> EvidenceEnvelope:
        store = panel_store.get_panel_store()
        store.append_panel(panel_type, panel_payload, steward_identity=steward_identity)
        envelope = EvidenceEnvelope(
            evidence_class="governance",
            event_type="panel_emitted",
            payload={"panel_type": panel_type, "panel": panel_payload},
            steward_identity=steward_identity,
            law_eval_id=law_eval_id,
            mission_id=mission_id,
            execution_id=execution_id,
        )
        self.emit(envelope)
        return envelope


_FACTORY: EvidenceFactory | None = None


def get_evidence_factory() -> EvidenceFactory:
    global _FACTORY
    if _FACTORY is None:
        _FACTORY = EvidenceFactory()
    return _FACTORY


def reset_evidence_factory(factory: EvidenceFactory | None = None) -> None:
    global _FACTORY
    _FACTORY = factory
