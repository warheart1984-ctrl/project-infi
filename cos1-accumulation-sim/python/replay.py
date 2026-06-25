"""Replay COS-1 Event Log v0.1 (events.jsonl) through the Python accumulation model."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cos1_model import (
    JPSSContributionEvent,
    has_reached_mat3,
    ingest_event,
    initial_state,
)

SIM_ROOT = Path(__file__).resolve().parents[1]


def replay(file_path: Path) -> None:
    state = initial_state()
    with file_path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            ev = JPSSContributionEvent(
                id=raw["id"],
                actor=raw["actor"],
                timestamp=raw["timestamp"],
                source_text=raw.get("sourceText", ""),
                from_exposure=raw["fromExposure"],
                accumulation_type=raw["accumulationType"],
                targets_layer=raw["targetsLayer"],
                builds_on=list(raw.get("buildsOn", [])),
            )
            state = ingest_event(state, ev)
            print(
                {
                    "event": ev.id,
                    "accumulationCount": state.accumulation_count,
                    "distinctActors": len(state.multi_person_actors),
                    "MAT3": has_reached_mat3(state),
                }
            )


def main() -> None:
    file_arg = sys.argv[1] if len(sys.argv) > 1 else str(SIM_ROOT / "events.jsonl")
    replay(Path(file_arg))


if __name__ == "__main__":
    main()
