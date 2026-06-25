"""Mission #002-grade observer packets for constitutionally closed URG missions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from constitutional.runtime import ObserverVerificationEngine

from src.ugr.mission.csr_bridge import MISSION_STATE_TYPE
from src.ugr.state_runtime import CSR

PACKET_ROOT = Path(".runtime/observer_packets/missions")
_STANDARD_DIRS = ("state", "receipts", "observer")


def _packet_readme(mission_id: str, verification: Any) -> str:
    diverged = verification.verification.divergence_detected
    failure_count = len(verification.failures)
    verdict = "PASS" if not diverged and failure_count == 0 else "REVIEW REQUIRED"
    return f"""# Observer Packet — URG Mission `{mission_id}`

Mission #002-grade verification bundle for a governed URG mission.

## Layout

| Path | Contents |
|------|----------|
| `state/mission_state.json` | Constitutional `StateObject` at close |
| `state/state_replay.json` | CSR replay result |
| `receipts/mission_receipts.jsonl` | Transition Receipt v2 for this mission |
| `observer/verification_report.json` | `ObserverVerificationEngine` verdict |
| `observer/instructions.md` | This file |

## Quick verdict

- **Status:** {verdict}
- **divergence_detected:** {diverged}
- **observer failures:** {failure_count}

## Verify locally

```bash
observer load-packet ./mission002_packet
observer verify {mission_id}
```
"""


def write_observer_packet_for_mission(mission_id: str) -> Path:
    """Write Mission #002-grade packet under `.runtime/observer_packets/missions/<id>/`."""
    PACKET_ROOT.mkdir(parents=True, exist_ok=True)
    packet_dir = PACKET_ROOT / mission_id
    for sub in _STANDARD_DIRS:
        (packet_dir / sub).mkdir(parents=True, exist_ok=True)

    state = CSR.get_state(mission_id)
    replay_result = CSR.replay(mission_id)
    observer = ObserverVerificationEngine(CSR)
    verification = observer.verify_state(mission_id)
    receipts = CSR.receipts_for(mission_id)

    (packet_dir / "state" / "mission_state.json").write_text(
        state.model_dump_json(indent=2),
        encoding="utf-8",
    )
    (packet_dir / "state" / "state_replay.json").write_text(
        replay_result.model_dump_json(indent=2),
        encoding="utf-8",
    )
    receipts_path = packet_dir / "receipts" / "mission_receipts.jsonl"
    with receipts_path.open("w", encoding="utf-8") as handle:
        for receipt in receipts:
            handle.write(receipt.model_dump_json() + "\n")

    (packet_dir / "observer" / "verification_report.json").write_text(
        verification.model_dump_json(indent=2),
        encoding="utf-8",
    )
    instructions = _packet_readme(mission_id, verification)
    (packet_dir / "observer" / "instructions.md").write_text(instructions, encoding="utf-8")

    # Flat index for observer CLI load-packet
    index = {
        "state_id": mission_id,
        "state_type": MISSION_STATE_TYPE,
        "packet_version": "mission-002",
        "paths": {
            "state": "state/mission_state.json",
            "replay": "state/state_replay.json",
            "receipts": "receipts/mission_receipts.jsonl",
            "verification": "observer/verification_report.json",
        },
    }
    (packet_dir / "packet_index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    return packet_dir
