"""Library Standing — epistemic tier over AAIS discovery contributions."""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Literal

ClaimLabel = Literal["denied", "hypothetical", "asserted", "proven", "rejected"]


class Standing(IntEnum):
    DENIED = 0
    HYPOTHETICAL = 1
    ASSERTED = 2
    PROVEN = 3


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


def standing_from_label(label: str | None) -> Standing:
    key = str(label or "asserted").strip().lower()
    if key == "rejected":
        return Standing.DENIED
    return LABEL_TO_STANDING.get(key, Standing.ASSERTED)


def label_from_standing(standing: Standing | int) -> str:
    value = int(standing)
    return STANDING_LABELS.get(value, "asserted")


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
) -> dict[str, Any]:
    out = dict(payload)
    s = Standing(int(standing))
    out["standing"] = int(s)
    out["claim_label"] = claim_label or label_from_standing(s)
    return out
