"""Mission #002-grade observer packets for constitutionally closed operator tasks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from constitutional.runtime import ObserverVerificationEngine, ObserverVerificationReport

from operator_kernel.csr import CSR
from operator_kernel.receipts_store import load_receipts_for_state

PACKET_ROOT = Path(".runtime/observer_packets")
OPERATOR_STATE_TYPE = "operator_task"

_STANDARD_FILES = ("state.json", "receipts.json", "replay.json", "verification.json", "README.md")


def _packet_readme(task_id: str, verification: ObserverVerificationReport) -> str:
    diverged = verification.verification.divergence_detected
    failure_count = len(verification.failures)
    verdict = "PASS" if not diverged and failure_count == 0 else "REVIEW REQUIRED"
    return f"""# Observer Packet — Operator Task `{task_id}`

Mission #002-grade verification bundle for a single governed operator task.

## Files

| File | Contents |
|------|----------|
| `state.json` | Constitutional `StateObject` at close |
| `receipts.json` | All Receipt v2 (transition receipts) for this task |
| `replay.json` | CSR replay result (canonical vs reconstructed) |
| `verification.json` | `ObserverVerificationEngine` verdict |

## Quick verdict

- **Status:** {verdict}
- **divergence_detected:** {diverged}
- **observer failures:** {failure_count}

## How to verify (outsider, no founder context)

1. Load `state.json` and `receipts.json`.
2. Reconstruct state by applying transitions in `receipts.json` order.
3. Open `replay.json` and confirm `diverged` is `false`.
4. Open `verification.json` and confirm `verification.divergence_detected` is `false`.
5. Compare reconstructed `current_state` to `state.json` → `current_state`.

## Receipt store (source)

Per-state append log:

```
.runtime/receipts/by_state/operator_task__{task_id}.jsonl
```
"""


def write_observer_packet_for_task(task_id: str) -> Path:
    """Write Mission #002-grade packet under `.runtime/observer_packets/<task_id>/`."""
    PACKET_ROOT.mkdir(parents=True, exist_ok=True)
    packet_dir = PACKET_ROOT / task_id
    packet_dir.mkdir(parents=True, exist_ok=True)

    state = CSR.get_state(task_id)
    replay_result = CSR.replay(task_id)

    observer = ObserverVerificationEngine(CSR)
    verification = observer.verify_state(task_id)

    receipts = load_receipts_for_state(OPERATOR_STATE_TYPE, task_id)
    if not receipts:
        receipts = CSR.receipts_for(task_id)

    (packet_dir / "state.json").write_text(state.model_dump_json(indent=2), encoding="utf-8")
    (packet_dir / "replay.json").write_text(
        replay_result.model_dump_json(indent=2),
        encoding="utf-8",
    )
    (packet_dir / "receipts.json").write_text(
        json.dumps([r.model_dump() for r in receipts], indent=2),
        encoding="utf-8",
    )
    (packet_dir / "verification.json").write_text(
        verification.model_dump_json(indent=2),
        encoding="utf-8",
    )
    (packet_dir / "README.md").write_text(
        _packet_readme(task_id, verification),
        encoding="utf-8",
    )
    return packet_dir


def _record_observer_packet(
    task_id: str,
    meta: dict[str, Any],
    packet_dir: Path,
) -> None:
    meta["constitutional_observer_packet"] = str(packet_dir)
    meta["constitutional_state"] = CSR.get_state(task_id).current_state


def constitutional_close_task(
    task_id: str,
    meta: dict[str, Any],
    *,
    kind: str,
    legal_basis: str,
    payload: dict[str, Any] | None = None,
) -> Path:
    """Set operator status closed, sync CSR to Closed, emit observer packet."""
    from operator_kernel.status_mapping import sync_operator_status_to_csr

    meta["status"] = "closed"
    sync_operator_status_to_csr(
        CSR,
        task_id,
        meta,
        kind=kind,
        legal_basis=legal_basis,
        payload=payload,
    )
    packet_dir = write_observer_packet_for_task(task_id)
    _record_observer_packet(task_id, meta, packet_dir)
    return packet_dir


def emit_observer_packet_if_closed(task_id: str, meta: dict[str, Any]) -> Path | None:
    """Emit packet when CSR is already at Closed (e.g. cancelled)."""
    try:
        state = CSR.get_state(task_id)
    except KeyError:
        return None
    if state.current_state != "Closed":
        return None
    packet_dir = write_observer_packet_for_task(task_id)
    _record_observer_packet(task_id, meta, packet_dir)
    return packet_dir


def constitutional_fail_task(
    task_id: str,
    meta: dict[str, Any],
    *,
    legal_basis: str,
    payload: dict[str, Any] | None = None,
) -> Path | None:
    """Advance failed task Observed → Closed and emit observer packet."""
    from operator_kernel.status_mapping import advance_to_constitutional_state

    current = CSR.get_state(task_id).current_state
    if current != "Observed":
        return None
    advance_to_constitutional_state(
        CSR,
        task_id,
        "Closed",
        kind="Closure",
        legal_basis=legal_basis,
        payload=payload,
    )
    meta["status"] = "closed"
    meta["constitutional_state"] = CSR.get_state(task_id).current_state
    packet_dir = write_observer_packet_for_task(task_id)
    _record_observer_packet(task_id, meta, packet_dir)
    return packet_dir
