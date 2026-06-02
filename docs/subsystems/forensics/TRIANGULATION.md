# Forensic Triangulation

Status: **partial live** — CLI correlator MVP; Jarvis tool route deferred.

CISIV stage: **implementation** (verification proof: `docs/proof/forensics/TRIANGULATION_V1_PROOF.md`)

## Purpose

Correlate Mechanic, Scorpion, and optional Slingshot diagnostic claims per shared `case_id` into `triangulation.v1` artifacts with temporal and invariant-overlap edges.

## Runtime

| Surface | Location |
|---------|----------|
| Package | `triangulation/` |
| CLI | `python -m triangulation correlate --case-id <id> [--fixture tri-demo-001]` |
| Output | `.runtime/triangulation/<case_id>/triangulation.v1.json` |
| Bridge map | `triangulation/bridge_map.json` |
| Fixture | `triangulation/fixtures/tri-demo-001/` |
| Gate | `make triangulation-gate` |

## Verification

```bash
make triangulation-gate
python -m triangulation correlate --case-id tri-demo-001 --fixture tri-demo-001
```

## Deferred

- Jarvis `forensic_triangulation` tool envelope (MECH-CHAT-01)
- Cross-machine replay manifests

## Related

- Concept origin: [../../_future/ideas_pending/FORENSIC_TRIANGULATION.md](../../_future/ideas_pending/FORENSIC_TRIANGULATION.md)
- Proof: [../../proof/forensics/TRIANGULATION_V1_PROOF.md](../../proof/forensics/TRIANGULATION_V1_PROOF.md)
