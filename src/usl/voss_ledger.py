"""Append-only USL ledger (separate from UGR Merkle)."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.usl.canonical_serialize import event_hash, ledger_root
from src.usl.signing import attach_signature
from src.usl.types import VossTransition

GENESIS_ROOT = (
    "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)


@dataclass
class Ledger:
    """Single-writer append chain per usl_node_id."""

    usl_node_id: str
    root: str = GENESIS_ROOT
    events: list[VossTransition] = field(default_factory=list)

    def append(
        self, transition: VossTransition, *, sign: bool = False
    ) -> VossTransition:
        """Finalize crypto fields and append to chain."""
        transition.crypto.prev_ledger_root = self.root
        transition.crypto.event_hash = event_hash(transition)
        if sign:
            attach_signature(transition)
        transition.crypto.ledger_root = ledger_root(
            self.root, transition.crypto.event_hash
        )
        self.root = transition.crypto.ledger_root
        self.events.append(transition)
        return transition

    def verify_chain(self) -> bool:
        """Verify event hashes and root chaining."""
        expected_root = GENESIS_ROOT
        for transition in self.events:
            if transition.crypto.prev_ledger_root != expected_root:
                return False
            computed_event = event_hash(transition)
            if transition.crypto.event_hash != computed_event:
                return False
            computed_root = ledger_root(expected_root, computed_event)
            if transition.crypto.ledger_root != computed_root:
                return False
            expected_root = computed_root
        if self.root != expected_root:
            return False
        return True

    def __len__(self) -> int:
        return len(self.events)
