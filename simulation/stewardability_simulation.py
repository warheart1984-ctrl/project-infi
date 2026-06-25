"""Minimal stewardability simulation — watch continuity succeed or fail."""

from __future__ import annotations

from src.continuity.stewardability.emergence_protocol import EmergenceCandidate
from src.continuity.stewardability.operating_conditions import bad_conditions, good_conditions
from src.continuity.stewardability.register import StewardDemonstration
from src.cos1.continuity_os import ContinuityOS


def sample_demonstration(
    lineage_impact: str = "STRENGTHENED",
) -> StewardDemonstration:
    return StewardDemonstration(
        steward_id="candidate-1",
        questions_asked=[
            "What should persist?",
            "What should evolve?",
            "Who decides?",
            "How is that decision justified?",
        ],
        reconstructions=["purpose", "identity", "judgment", "constitution"],
        critiques=["identified drift in invariant classification"],
        adaptations=["proposed boundary refinement"],
        lineage_impact=lineage_impact,  # type: ignore[arg-type]
    )


def run_simulation() -> None:
    os = ContinuityOS()

    print("=== Phase 1: healthy stewardability, strong candidate emerges ===")
    result = os.step(
        good_conditions(),
        EmergenceCandidate(id="c1", name="Future Steward", background="JPSS student"),
        sample_demonstration("STRENGTHENED"),
    )
    print("Continuity state:", result.continuity_state.model_dump())
    print("Continuity succeeded?", result.continuity_succeeded)
    print("Drift signals:", [signal.kind for signal in result.drift_signals])

    print("\n=== Phase 2: conditions degrade, no new stewards emerge ===")
    for _ in range(3):
        result = os.step(bad_conditions())
    print("Continuity state:", result.continuity_state.model_dump())
    print("Continuity succeeded?", result.continuity_succeeded)
    print("Drift signals:", [f"{signal.kind} ({signal.severity})" for signal in result.drift_signals])


if __name__ == "__main__":
    run_simulation()
