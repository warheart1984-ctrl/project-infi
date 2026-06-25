"""Compounding chain detector — multi-person, multi-event chains for MAT-3."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.cos1.accumulation.ae_json_schema import AccumulationEvent, AccumulationSignature

MAT3_MIN_ACTORS = 2
MAT3_MIN_CHAIN_LENGTH = 2


class ClassifiedAccumulationEvent(BaseModel):
    """Minimal event shape for chain detection."""

    event_id: str
    actor_id: str
    accumulation_signature: AccumulationSignature
    builds_on_event_ids: list[str] = Field(default_factory=list)

    @classmethod
    def from_accumulation_event(cls, event: AccumulationEvent) -> ClassifiedAccumulationEvent:
        sig = event.accumulation.signature or "NONE"
        return cls(
            event_id=event.event_id,
            actor_id=event.actor.id,
            accumulation_signature=sig,
            builds_on_event_ids=list(event.accumulation.builds_on_event_ids),
        )


class CompoundingChain(BaseModel):
    chain: list[str] = Field(default_factory=list)
    actors: list[str] = Field(default_factory=list)
    signatures: list[AccumulationSignature] = Field(default_factory=list)

    @property
    def length(self) -> int:
        return len(self.chain)

    @property
    def multi_actor(self) -> bool:
        return len(set(self.actors)) >= MAT3_MIN_ACTORS


class MAT3Assessment(BaseModel):
    """Multi-actor compounding threshold — lineage self-evolving via generational chains."""

    threshold_met: bool
    qualifying_chains: list[CompoundingChain] = Field(default_factory=list)
    max_chain_length: int = 0
    multi_actor_chain_count: int = 0
    a4_event_count: int = 0
    blockers: list[str] = Field(default_factory=list)


def detect_compounding_chains(
    events: list[ClassifiedAccumulationEvent],
) -> list[CompoundingChain]:
    """Detect directed compounding chains Event A → B → C where each builds on prior."""
    event_map = {event.event_id: event for event in events}
    chains: list[CompoundingChain] = []
    seen: set[tuple[str, ...]] = set()

    for event in events:
        if not event.builds_on_event_ids:
            continue

        for parent_id in event.builds_on_event_ids:
            chain_ids = [parent_id, event.event_id]
            actor_set = {
                event_map.get(parent_id).actor_id if event_map.get(parent_id) else "",
                event.actor_id,
            }
            sigs = [
                event_map.get(parent_id).accumulation_signature
                if event_map.get(parent_id)
                else "NONE",
                event.accumulation_signature,
            ]

            current = event.event_id
            while True:
                next_event = next(
                    (candidate for candidate in events if current in candidate.builds_on_event_ids),
                    None,
                )
                if next_event is None:
                    break
                chain_ids.append(next_event.event_id)
                actor_set.add(next_event.actor_id)
                sigs.append(next_event.accumulation_signature)
                current = next_event.event_id

            key = tuple(chain_ids)
            if key in seen:
                continue
            seen.add(key)

            chains.append(
                CompoundingChain(
                    chain=chain_ids,
                    actors=sorted(actor for actor in actor_set if actor),
                    signatures=[sig for sig in sigs if sig],
                )
            )

    return chains


def assess_mat3(events: list[ClassifiedAccumulationEvent]) -> MAT3Assessment:
    """MAT-3: multi-person compounding chains indicate generational self-evolution."""
    chains = detect_compounding_chains(events)
    multi_actor = [chain for chain in chains if chain.multi_actor]
    a4_count = sum(1 for event in events if event.accumulation_signature == "A4")
    max_len = max((chain.length for chain in chains), default=0)

    blockers: list[str] = []
    if not multi_actor:
        blockers.append(
            f"No compounding chain with ≥ {MAT3_MIN_ACTORS} distinct actors."
        )
    if max_len < MAT3_MIN_CHAIN_LENGTH:
        blockers.append(
            f"No chain length ≥ {MAT3_MIN_CHAIN_LENGTH}."
        )

    threshold_met = bool(multi_actor) and max_len >= MAT3_MIN_CHAIN_LENGTH

    return MAT3Assessment(
        threshold_met=threshold_met,
        qualifying_chains=multi_actor,
        max_chain_length=max_len,
        multi_actor_chain_count=len(multi_actor),
        a4_event_count=a4_count,
        blockers=blockers if not threshold_met else [],
    )
