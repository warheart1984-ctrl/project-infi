"""Mission #003 — External Reproduction Protocol (M3-A)."""

from __future__ import annotations

from src.crk1.external_reproduction_harness import (
    ExternalReproductionHarness,
    prepare_continuity_substrate,
)


def test_external_reproduction_harness_passes(runtime) -> None:
    report = ExternalReproductionHarness(runtime).run_all()
    assert report.passed, report.summary()


def test_prepare_continuity_substrate_enables_semantic_audit(runtime) -> None:
    prepare_continuity_substrate(runtime)
    admitted = runtime.list_interpreted_evidence()
    assert len(admitted) >= 1
    assert len(runtime.get_all_interpretations()) >= 2


def test_reproduction_steps_are_named(runtime) -> None:
    report = ExternalReproductionHarness(runtime).run_all()
    step_ids = [step.step_id for step in report.steps]
    assert step_ids == [
        "REP-0",
        "REP-1",
        "REP-2",
        "REP-3",
        "REP-4",
        "REP-5",
        "REP-6",
        "REP-7",
        "REP-8",
        "REP-9",
    ]
