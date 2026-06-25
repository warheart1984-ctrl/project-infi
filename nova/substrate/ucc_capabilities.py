from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from nova.law_kernel.models import Intent
from nova.lineage.ucc_emit import emit_ucc_event


@dataclass
class UCCConstraints:
    max_tokens: int | None = None
    requires_pacing_consent: bool = True
    overload_safe: bool = True
    cognitive_style_safe: bool = True


@dataclass
class UCCCapabilityContract:
    name: str
    handler: Callable[[Intent], Any]
    invariants: dict[str, Callable[[Intent], bool]]
    ucc: UCCConstraints


class UCCSubstrateRegistry:
    OVERLOAD_BLOCK_THRESHOLD = 0.8

    def __init__(self) -> None:
        self._caps: dict[str, UCCCapabilityContract] = {}

    def register(self, contract: UCCCapabilityContract) -> None:
        self._caps[contract.name] = contract

    def execute(
        self,
        intent: Intent,
        *,
        overload_score: float,
        pacing_ok: bool,
        cognitive_style: str,
    ) -> Any:
        cap = intent.payload.get("capability")
        if cap not in self._caps:
            raise RuntimeError("Unknown capability")

        contract = self._caps[cap]

        if contract.ucc.requires_pacing_consent and not pacing_ok:
            raise RuntimeError("Pacing consent not granted")

        if contract.ucc.overload_safe and overload_score > self.OVERLOAD_BLOCK_THRESHOLD:
            raise RuntimeError("Overload too high for this capability")

        for name, inv in contract.invariants.items():
            if not inv(intent):
                raise RuntimeError(f"Invariant failed: {name}")

        result = contract.handler(intent)

        emit_ucc_event(
            kind="UCC_CAPABILITY_EXEC",
            actor_id=intent.origin,
            intent_id=intent.id,
            cognitive_style=cognitive_style,
            overload_score=overload_score,
            pacing_ok=pacing_ok,
            capability=str(cap),
        )

        return result
