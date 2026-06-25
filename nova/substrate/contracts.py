from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from nova.law_kernel.models import Intent


@dataclass
class CapabilityContract:
    name: str
    handler: Callable[[Intent], Any]
    invariants: dict[str, Callable[[Intent], bool]]


class SubstrateRegistry:
    def __init__(self) -> None:
        self._caps: dict[str, CapabilityContract] = {}

    def register(self, contract: CapabilityContract) -> None:
        self._caps[contract.name] = contract

    def execute(self, intent: Intent) -> Any:
        cap = intent.payload.get("capability")
        if cap not in self._caps:
            raise RuntimeError("Unknown capability")
        contract = self._caps[cap]
        for name, inv in contract.invariants.items():
            if not inv(intent):
                raise RuntimeError(f"Invariant failed: {name}")
        return contract.handler(intent)
