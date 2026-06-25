"""CDP-1 experiment harness tests."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "sdk" / "continuity-sdk"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SDK) not in sys.path:
    sys.path.insert(0, str(SDK))

from harness.cdp1_experiment import CDP1Experiment, validate_cdp1_run


@dataclass
class _SimulatedSteward:
    id: str
    phase: str = "pre"
    replayed: bool = field(default=False, init=False)

    def isolation_material(self) -> str:
        return f"isolated:{self.id}"

    def replay_lineage(self, crr: dict, clg: dict) -> None:
        self.replayed = True
        self.phase = "post"

    def task_trace(self) -> dict:
        if self.phase == "pre":
            return {"prediction_error": 0.7, "calibration_aligned": False}
        return {"prediction_error": 0.0, "calibration_aligned": True}


def test_cdp1_experiment_passes_assimilation() -> None:
    steward = _SimulatedSteward("steward_s2_independent")

    def task(s: _SimulatedSteward) -> dict:
        return s.task_trace()

    experiment = CDP1Experiment(
        task=task,
        threshold=0.15,
        original_participant_ids=["steward_llm", "steward_human", "steward_agent"],
    )
    crr = {"event": "fall_calibration", "reality": 0.3}
    clg = {"lineage": ["crr-1", "crr-2", "crr-3"]}

    result = experiment.run(steward, crr, clg)
    assert steward.replayed
    assert result.delta >= 0.15
    assert result.continuity_passed

    report = validate_cdp1_run(result)
    assert report["decision"] == "PASS"


def test_cdp1_rejects_participant_steward() -> None:
    steward = _SimulatedSteward("steward_llm")
    experiment = CDP1Experiment(
        task=lambda s: {"prediction_error": 0.5, "calibration_aligned": False},
        threshold=0.1,
        original_participant_ids=["steward_llm"],
    )
    with pytest.raises(ValueError, match="isolation failed"):
        experiment.run(steward, {"event": "x"}, {"lineage": []})
