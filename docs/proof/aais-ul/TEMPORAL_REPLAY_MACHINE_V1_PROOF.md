# Temporal Replay Machine v1 Proof

Status: **governed** — law-pinned operator replay (read-only default).

## Claim

Operators can scrub a mission (or other subject) timeline, pin law at timestamp T, verify Merkle/receipt alignment, dry-run forward replay, and export a replay bundle.

## Verification

```bash
make temporal-replay-gate
python -m pytest tests/test_temporal_replay.py tests/test_operator_replay_api_shapes.py -q
```

## API smoke

```bash
curl "http://127.0.0.1:5000/api/operator/replay/mission/<mission_id>/timeline"
curl "http://127.0.0.1:5000/api/operator/replay/mission/<mission_id>/state?at=2026-06-04T14:32:00+00:00"
curl -X POST "http://127.0.0.1:5000/api/operator/replay/mission/<mission_id>/verify" -H "Content-Type: application/json" -d "{\"at\":\"2026-06-04T14:32:00+00:00\"}"
```

## UI

- `/operator/replay` — Replay Machine shell
- `/operator/replay/mission/<mission_id>` — deep link from Jarvis Mission Replay card

## Implementation map

| Component | Path |
|-----------|------|
| Kernel | `src/temporal_replay/` |
| Schemas | `schemas/temporal_replay_event.v1.json`, `schemas/temporal_replay_bundle.v1.json` |
| Routes | `src/api.py` `/api/operator/replay/*` |
| Bridge audit persist | `src/temporal_replay/bridge_audit.py` |
