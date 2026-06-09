"""Library Standing — epistemic tier over AAIS discovery contributions."""

from __future__ import annotations

from enum import Enum, IntEnum
from typing import Any, Literal

ClaimLabel = Literal["denied", "hypothetical", "asserted", "proven", "rejected"]


class Standing(IntEnum):
    DENIED = 0
    HYPOTHETICAL = 1
    ASSERTED = 2
    PROVEN = 3


class EpistemicState(str, Enum):
    """Canonical 3-state epistemic layer mapped from 4-band Standing."""

    REJECTED = "rejected"
    PENDING = "pending"
    PROVEN = "proven"


STANDING_LABELS: dict[int, str] = {
    Standing.DENIED: "denied",
    Standing.HYPOTHETICAL: "hypothetical",
    Standing.ASSERTED: "asserted",
    Standing.PROVEN: "proven",
}

LABEL_TO_STANDING: dict[str, Standing] = {
    "denied": Standing.DENIED,
    "hypothetical": Standing.HYPOTHETICAL,
    "asserted": Standing.ASSERTED,
    "proven": Standing.PROVEN,
}

EPISTEMIC_TO_STANDING: dict[EpistemicState, Standing] = {
    EpistemicState.REJECTED: Standing.DENIED,
    EpistemicState.PENDING: Standing.ASSERTED,
    EpistemicState.PROVEN: Standing.PROVEN,
}

STANDING_TO_EPISTEMIC: dict[Standing, EpistemicState] = {
    Standing.DENIED: EpistemicState.REJECTED,
    Standing.HYPOTHETICAL: EpistemicState.PENDING,
    Standing.ASSERTED: EpistemicState.PENDING,
    Standing.PROVEN: EpistemicState.PROVEN,
}


def standing_from_label(label: str | None) -> Standing:
    key = str(label or "asserted").strip().lower()
    if key == "rejected":
        return Standing.DENIED
    return LABEL_TO_STANDING.get(key, Standing.ASSERTED)


def label_from_standing(standing: Standing | int) -> str:
    value = int(standing)
    return STANDING_LABELS.get(value, "asserted")


def epistemic_from_standing(
    standing: Standing | int,
    *,
    claim_label: str | None = None,
    rejection_source: str | None = None,
) -> EpistemicState:
    if rejection_source:
        return EpistemicState.REJECTED
    label = str(claim_label or "").strip().lower()
    if label == "rejected":
        return EpistemicState.REJECTED
    try:
        band = Standing(int(standing))
    except (TypeError, ValueError):
        band = Standing.ASSERTED
    if band == Standing.DENIED:
        return EpistemicState.REJECTED
    return STANDING_TO_EPISTEMIC.get(band, EpistemicState.PENDING)


def standing_from_epistemic(state: EpistemicState | str) -> Standing:
    try:
        ep = state if isinstance(state, EpistemicState) else EpistemicState(str(state))
    except ValueError:
        return Standing.ASSERTED
    return EPISTEMIC_TO_STANDING.get(ep, Standing.ASSERTED)


def epistemic_from_receipt(receipt: dict[str, Any]) -> EpistemicState:
    payload = dict(receipt.get("payload") or {})
    proof = dict(receipt.get("proof") or {})
    if payload.get("epistemic_state"):
        try:
            return EpistemicState(str(payload["epistemic_state"]))
        except ValueError:
            pass
    return epistemic_from_standing(
        standing_from_receipt(receipt),
        claim_label=str(payload.get("claim_label") or proof.get("claim_label") or ""),
        rejection_source=str(payload.get("rejection_source") or proof.get("rejection_source") or "") or None,
    )


def is_library_admitted_epistemic(state: EpistemicState | str) -> bool:
    try:
        ep = state if isinstance(state, EpistemicState) else EpistemicState(str(state))
    except ValueError:
        return False
    return ep in (EpistemicState.PENDING, EpistemicState.PROVEN)


def is_operator_promotable(state: EpistemicState | str) -> bool:
    try:
        ep = state if isinstance(state, EpistemicState) else EpistemicState(str(state))
    except ValueError:
        return False
    return ep == EpistemicState.PROVEN


def is_immutable_epistemic(state: EpistemicState | str) -> bool:
    try:
        ep = state if isinstance(state, EpistemicState) else EpistemicState(str(state))
    except ValueError:
        return False
    return ep in (EpistemicState.REJECTED, EpistemicState.PROVEN)


def build_epistemic_envelope(
    standing: Standing | int,
    *,
    claim_label: str | None = None,
    rejection_source: str | None = None,
    falsity_fingerprint: str | None = None,
    pod_id: str | None = None,
    contribution_id: str | None = None,
    promoted_to_operator: bool | None = None,
    promotion_event_id: str | None = None,
) -> dict[str, Any]:
    s = Standing(int(standing))
    label = claim_label or label_from_standing(s)
    ep = epistemic_from_standing(s, claim_label=label, rejection_source=rejection_source)
    envelope: dict[str, Any] = {
        "epistemic_state": ep.value,
        "standing": int(s),
        "claim_label": label,
    }
    if rejection_source:
        envelope["rejection_source"] = rejection_source
    if falsity_fingerprint:
        envelope["falsity_fingerprint"] = falsity_fingerprint
    if pod_id:
        envelope["pod_id"] = pod_id
    if contribution_id:
        envelope["contribution_id"] = contribution_id
    if promoted_to_operator is not None:
        envelope["promoted_to_operator"] = promoted_to_operator
    if promotion_event_id:
        envelope["promotion_event_id"] = promotion_event_id
    return envelope


def library_admitted(standing: Standing | int | str | None) -> bool:
    if standing is None:
        return True
    if isinstance(standing, str):
        return standing_from_label(standing) >= Standing.HYPOTHETICAL
    return int(standing) >= int(Standing.HYPOTHETICAL)


def has_authority(standing: Standing | int | str | None) -> bool:
    if standing is None:
        return False
    if isinstance(standing, str):
        return standing_from_label(standing) >= Standing.ASSERTED
    return int(standing) >= int(Standing.ASSERTED)


def reward_tier(standing: Standing | int | str | None) -> str:
    if standing is None:
        return "asserted"
    if isinstance(standing, str):
        s = standing_from_label(standing)
    else:
        s = Standing(int(standing))
    if s == Standing.DENIED:
        return "denied"
    if s == Standing.HYPOTHETICAL:
        return "hypothetical"
    if s == Standing.PROVEN:
        return "proven"
    return "asserted"


def standing_from_receipt(receipt: dict[str, Any]) -> Standing:
    payload = dict(receipt.get("payload") or {})
    proof = dict(receipt.get("proof") or {})
    if "standing" in payload:
        try:
            return Standing(int(payload["standing"]))
        except (TypeError, ValueError):
            pass
    if "standing" in proof:
        try:
            return Standing(int(proof["standing"]))
        except (TypeError, ValueError):
            pass
    return standing_from_label(
        str(payload.get("claim_label") or proof.get("claim_label") or "asserted")
    )


def enrich_payload_with_standing(
    payload: dict[str, Any],
    *,
    standing: Standing | int,
    claim_label: str | None = None,
    rejection_source: str | None = None,
    falsity_fingerprint: str | None = None,
    pod_id: str | None = None,
    contribution_id: str | None = None,
) -> dict[str, Any]:
    out = dict(payload)
    s = Standing(int(standing))
    label = claim_label or label_from_standing(s)
    out["standing"] = int(s)
    out["claim_label"] = label
    out["epistemic_state"] = epistemic_from_standing(
        s,
        claim_label=label,
        rejection_source=rejection_source,
    ).value
    if rejection_source:
        out["rejection_source"] = rejection_source
    if falsity_fingerprint:
        out["falsity_fingerprint"] = falsity_fingerprint
    if pod_id and not out.get("discovery_pod_id"):
        out["discovery_pod_id"] = pod_id
    if contribution_id and not out.get("contribution_id"):
        out["contribution_id"] = contribution_id
    return out
