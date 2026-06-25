from cos1_model import (
    JPSSContributionEvent,
    RAState,
    has_reached_mat3,
    ingest_event,
    initial_state,
    now_iso,
)


def print_state(label: str, state: RAState) -> None:
    print(
        label,
        {
            "accumulationCount": state.accumulation_count,
            "distinctActors": len(state.multi_person_actors),
            "MAT3": has_reached_mat3(state),
        },
    )


def main() -> None:
    state: RAState = initial_state()

    jon_a2 = JPSSContributionEvent(
        id="E_JON_A2",
        actor="Jon",
        timestamp=now_iso(),
        source_text="Propagation / Convergence / Accumulation / Stewardability stack.",
        from_exposure=False,
        accumulation_type="A2",
        targets_layer="Continuity",
        builds_on=[],
    )

    sue_a1 = JPSSContributionEvent(
        id="E_SUE_A1",
        actor="Sue",
        timestamp=now_iso(),
        source_text="Calibration drift without knowledge loss.",
        from_exposure=True,
        accumulation_type="A1",
        targets_layer="Continuity",
        builds_on=["E_JON_A2"],
    )

    bradley_a2 = JPSSContributionEvent(
        id="E_BRADLEY_A2",
        actor="Bradley",
        timestamp=now_iso(),
        source_text=(
            "Judgment Categories / Judgment Transmission / Judgment Evolution + "
            "Judgment Lineage / Stewardship Record / Constitutional Precedent Record."
        ),
        from_exposure=True,
        accumulation_type="A2",
        targets_layer="Transferability",
        builds_on=["E_JON_A2"],
    )

    state = ingest_event(state, jon_a2)
    print_state("After Jon:", state)

    state = ingest_event(state, sue_a1)
    print_state("After Sue:", state)

    state = ingest_event(state, bradley_a2)
    print_state("After Bradley:", state)


if __name__ == "__main__":
    main()
