"""Tests for minimal cos1-accumulation-sim Python model (parity with TypeScript)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SIM_ROOT = Path(__file__).resolve().parents[1] / "cos1-accumulation-sim"
PYTHON_DIR = SIM_ROOT / "python"

sys.path.insert(0, str(PYTHON_DIR))

from cos1_model import (  # noqa: E402
    JPSSContributionEvent,
    has_reached_mat3,
    ingest_event,
    initial_state,
    now_iso,
)


def test_mat3_flips_on_third_event() -> None:
    state = initial_state()

    jon = JPSSContributionEvent(
        id="E_JON_A2",
        actor="Jon",
        timestamp=now_iso(),
        source_text="stack",
        from_exposure=False,
        accumulation_type="A2",
        targets_layer="Continuity",
        builds_on=[],
    )
    sue = JPSSContributionEvent(
        id="E_SUE_A1",
        actor="Sue",
        timestamp=now_iso(),
        source_text="calibration drift",
        from_exposure=True,
        accumulation_type="A1",
        targets_layer="Continuity",
        builds_on=["E_JON_A2"],
    )
    bradley = JPSSContributionEvent(
        id="E_BRADLEY_A2",
        actor="Bradley",
        timestamp=now_iso(),
        source_text="judgment transmission",
        from_exposure=True,
        accumulation_type="A2",
        targets_layer="Transferability",
        builds_on=["E_JON_A2"],
    )

    state = ingest_event(state, jon)
    assert has_reached_mat3(state) is False

    state = ingest_event(state, sue)
    assert has_reached_mat3(state) is False

    state = ingest_event(state, bradley)
    assert has_reached_mat3(state) is True
    assert state.accumulation_count == 3
    assert state.multi_person_actors == {"Jon", "Sue", "Bradley"}


def test_python_replay_jsonl() -> None:
    events_file = SIM_ROOT / "events.jsonl"
    result = subprocess.run(
        [sys.executable, str(PYTHON_DIR / "replay.py"), str(events_file)],
        cwd=PYTHON_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "E_BRADLEY_A2" in result.stdout
    assert "'MAT3': True" in result.stdout or '"MAT3": True' in result.stdout
