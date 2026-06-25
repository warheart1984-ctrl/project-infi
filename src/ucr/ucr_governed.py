"""UCR governed-mode trust invariants."""

from __future__ import annotations

from dataclasses import dataclass

from src.ucr.trust_root import TrustRoot, UCRTrustContext


@dataclass(frozen=True, slots=True)
class GovernedModeRefusal:
    reason_code: int
    reason_detail: str


def require_governed_mode(
    ucr_context: UCRTrustContext,
    kernel_trust_root: TrustRoot,
    *,
    ucr_law_view: str,
    ucr_corridor_view: str,
) -> GovernedModeRefusal | None:
    if not kernel_trust_root.h_trust_root:
        return GovernedModeRefusal(1006, "trust root missing")

    if ucr_context.h_trust_root != kernel_trust_root.h_trust_root:
        return GovernedModeRefusal(1006, "H_TRUST_ROOT mismatch")

    if ucr_context.h_law_spine != kernel_trust_root.h_law_spine:
        return GovernedModeRefusal(1006, "H_LAW_SPINE mismatch")

    if ucr_context.h_corridors != kernel_trust_root.h_corridors:
        return GovernedModeRefusal(1006, "H_CORRIDORS mismatch")

    if ucr_law_view != kernel_trust_root.h_law_spine:
        return GovernedModeRefusal(1006, "UCR law view mismatch")

    if ucr_corridor_view != kernel_trust_root.h_corridors:
        return GovernedModeRefusal(1006, "UCR corridor view mismatch")

    return None
