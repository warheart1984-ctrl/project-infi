from __future__ import annotations

from typing import Any

from nova.governance.steward_models import AmendmentProposal, RatifiedAmendment, StewardId, StewardSignature

_proposals: list[AmendmentProposal] = []
_ratifications: list[RatifiedAmendment] = []
_hydrated = False


def _ensure_hydrated() -> None:
    global _hydrated
    if _hydrated or _proposals or _ratifications:
        return
    try:
        from nova.bridges.panel_store import get_panel_store

        for event in get_panel_store().list_steward_events():
            kind = event.get("kind")
            if kind == "AMENDMENT_PROPOSAL":
                _proposals.append(
                    AmendmentProposal(
                        id=str(event.get("id") or ""),
                        steward_id=StewardId(str(event.get("steward_id") or "operator")),
                        payload=dict(event.get("payload") or {}),
                        status=str(event.get("status") or "proposed"),
                        created_at=str(event.get("created_at") or ""),
                        lineage_event_id=str(event.get("lineage_event_id") or ""),
                    )
                )
            elif kind == "AMENDMENT_RATIFIED":
                signatures = [
                    StewardSignature(
                        steward_id=StewardId(str(sig.get("steward_id") or "operator")),
                        signed_at=str(sig.get("signed_at") or ""),
                        t5_ref_signal_hash=str(sig.get("t5_ref_signal_hash") or ""),
                        lineage_event_id=str(sig.get("lineage_event_id") or ""),
                    )
                    for sig in event.get("signatures") or []
                ]
                _ratifications.append(
                    RatifiedAmendment(
                        proposal_id=str(event.get("proposal_id") or ""),
                        signatures=signatures,
                        payload=dict(event.get("payload") or {}),
                        ratified_at=str(event.get("ratified_at") or ""),
                        lineage_event_id=str(event.get("lineage_event_id") or ""),
                        t5_ref_signal_hash=str(event.get("t5_ref_signal_hash") or ""),
                    )
                )
    except Exception:
        pass
    _hydrated = True


def _persist_steward_event(event: dict[str, Any]) -> None:
    try:
        from nova.bridges.panel_store import get_panel_store

        get_panel_store().append_steward_event(event)
    except Exception:
        pass


class StewardLedger:
    """Append-only steward proposal and ratification ledger."""

    def record_proposal(self, proposal: AmendmentProposal) -> AmendmentProposal:
        _proposals.append(proposal)
        _persist_steward_event({"kind": "AMENDMENT_PROPOSAL", **proposal.to_dict()})
        return proposal

    def record_ratification(self, amendment: RatifiedAmendment) -> RatifiedAmendment:
        _ratifications.append(amendment)
        for proposal in _proposals:
            if proposal.id == amendment.proposal_id:
                proposal.status = "ratified"
        _persist_steward_event({"kind": "AMENDMENT_RATIFIED", **amendment.to_dict()})
        return amendment

    def list_active_amendments(self) -> list[RatifiedAmendment]:
        _ensure_hydrated()
        return list(_ratifications)

    def get_proposal(self, proposal_id: str) -> AmendmentProposal | None:
        _ensure_hydrated()
        for proposal in _proposals:
            if proposal.id == proposal_id:
                return proposal
        return None

    def list_proposals(self) -> list[AmendmentProposal]:
        _ensure_hydrated()
        return list(_proposals)


_default_ledger = StewardLedger()


def get_steward_ledger() -> StewardLedger:
    return _default_ledger


def clear_steward_ledger() -> None:
    global _hydrated
    _proposals.clear()
    _ratifications.clear()
    _hydrated = False
    try:
        from nova.bridges.panel_store import get_panel_store

        get_panel_store().clear_steward()
    except Exception:
        pass


def list_steward_events() -> list[dict[str, Any]]:
    _ensure_hydrated()
    events: list[dict[str, Any]] = []
    for proposal in _proposals:
        events.append({"kind": "AMENDMENT_PROPOSAL", **proposal.to_dict()})
    for amendment in _ratifications:
        events.append({"kind": "AMENDMENT_RATIFIED", **amendment.to_dict()})
    return events
