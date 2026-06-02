# Forensic Triangulation

Status: **partial live** — CLI correlator + Jarvis bridge/API.

CISIV stage: **implementation** (verification proof: `docs/proof/forensics/TRIANGULATION_V1_PROOF.md`)

## Purpose

Correlate Mechanic, Scorpion, and optional Slingshot diagnostic claims per shared `case_id` into `triangulation.v1` artifacts with temporal and invariant-overlap edges.

## Runtime

| Surface | Location |
|---------|----------|
| Package | `triangulation/` |
| CLI | `python -m triangulation correlate --case-id <id> [--fixture tri-demo-001]` |
| API | `POST /api/jarvis/triangulation/correlate` |
| Bridge | `forensic_triangulation` / `correlate` |
| Output | `.runtime/triangulation/<case_id>/triangulation.v1.json` |
| Bridge map | `triangulation/bridge_map.json` |
| Fixture | `triangulation/fixtures/tri-demo-001/` |
| Gate | `make triangulation-gate` |

## Verification

```bash
make triangulation-gate
python -m triangulation correlate --case-id tri-demo-001 --fixture tri-demo-001
python -m pytest tests/test_capability_bridge_alt3.py -q
```

## Deferred

- Cross-machine replay manifests

## Related

- Concept origin: [../../_future/ideas_pending/FORENSIC_TRIANGULATION.md](../../_future/ideas_pending/FORENSIC_TRIANGULATION.md)
- Proof: [../../proof/forensics/TRIANGULATION_V1_PROOF.md](../../proof/forensics/TRIANGULATION_V1_PROOF.md)
