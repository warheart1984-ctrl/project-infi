"""Creation operator Create: S → S enforcing LCI at runtime."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Callable

from src.continuity.continuity_lattice import lci_holds
from src.continuity.lineage import Lineage, continuity_trace, generativity


class LCIViolation(RuntimeError):
    """Creation blocked — would annihilate continuity or shrink generativity."""


class AdmissibleTransitionError(RuntimeError):
    """Creation blocked — transition not in admissible set T."""


@dataclass
class SubstrateState:
    """Runtime substrate state s ∈ S with extractable lineage."""

    state_id: str
    lineage: Lineage
    revision: int = 0
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "state_id": self.state_id,
            "revision": self.revision,
            "lineage": self.lineage.to_dict(),
            "attributes": dict(self.attributes),
        }


TransitionPredicate = Callable[[SubstrateState, SubstrateState], bool]


@dataclass
class CreationOperator:
    """Create(s) — the only lawful path for structural extension."""

    admissible: TransitionPredicate | None = None

    def create(
        self,
        state: SubstrateState,
        *,
        add_events: frozenset[str],
        generativity_delta: float = 1.0,
        meaning_class: str | None = None,
        attribute_patch: dict[str, Any] | None = None,
        next_state_id: str | None = None,
    ) -> SubstrateState:
        if generativity_delta < 0:
            raise LCIViolation("generativity_delta must be non-negative")

        next_events = continuity_trace(state.lineage) | add_events
        if next_events == continuity_trace(state.lineage) and generativity_delta == 0.0:
            raise LCIViolation("create must extend continuity or generativity")

        next_lineage = replace(
            state.lineage,
            event_ids=next_events,
            generativity=generativity(state.lineage) + generativity_delta,
            meaning_class=meaning_class or state.lineage.meaning_class,
        )

        if not lci_holds(state.lineage, next_lineage):
            raise LCIViolation(
                "LCI violated: continuity must grow and generativity must not decrease"
            )

        next_state = SubstrateState(
            state_id=next_state_id or f"{state.state_id}:r{state.revision + 1}",
            lineage=next_lineage,
            revision=state.revision + 1,
            attributes={**state.attributes, **(attribute_patch or {})},
        )

        if self.admissible is not None and not self.admissible(state, next_state):
            raise AdmissibleTransitionError("transition (s, s') ∉ T")

        return next_state


DEFAULT_CREATION_OPERATOR = CreationOperator()
