"""Tests for CRK-1 Drift Visualizer."""

from __future__ import annotations

from src.crk1.drift_visualizer import DriftVisualizer, exposure_to_char
from src.crk1.mutation_ledger import CRK1MutationLedger, ExposureSnapshot, MutationEntry


def test_exposure_glyphs() -> None:
    assert exposure_to_char(0.9) == "█"
    assert exposure_to_char(0.5) == "▇"
    assert exposure_to_char(0.2) == "▂"
    assert exposure_to_char(0.0) == "░"


def test_drift_visualizer_from_monitor_history(semantic_monitor) -> None:
    semantic_monitor.snapshot()
    semantic_monitor.simulate_drift()
    visualizer = DriftVisualizer.from_monitor_history(semantic_monitor.history, ce_values=[1.0, 1.0])
    rendered = visualizer.render()

    assert "CRK‑1 Drift Visualizer" in rendered
    assert "CE(S):" in rendered
    assert "SE(S):" in rendered
    assert "monotonic non‑decrease (K6)" in rendered
    assert not visualizer.detect_violations()


def test_drift_visualizer_from_mutation_ledger() -> None:
    ledger = CRK1MutationLedger()
    ledger.append(
        MutationEntry(
            proposer_identity="root",
            mutation_type="interpretation",
            exposure_before=ExposureSnapshot(ce=1.0, se=0.5),
            exposure_after=ExposureSnapshot(ce=1.0, se=0.6),
            constitutional=True,
        )
    )
    visualizer = DriftVisualizer.from_mutation_ledger(ledger)
    assert "█" in visualizer.render() or "▇" in visualizer.render()
