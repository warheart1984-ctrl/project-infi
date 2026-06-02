# Forensic Triangulation Ledger — MVP Plan

CISIV stage: concept → implementation target

Status: **implemented (partial live)** — see [../../subsystems/forensics/TRIANGULATION.md](../../subsystems/forensics/TRIANGULATION.md)

Concept origin: [./FORENSIC_TRIANGULATION.md](./FORENSIC_TRIANGULATION.md)

## 1. Minimal Runtime Surface

| Surface | Planned location | Notes |
|---------|------------------|-------|
| Package | `triangulation/` | Correlator module |
| CLI | `python -m triangulation correlate --case-id <id>` | Fixture-driven MVP |
| Output | `.runtime/triangulation/<case_id>/triangulation.v1.json` | Schema-validated |
| Bridge map | `triangulation/bridge_map.json` | Invariant overlap rules |
| Schema | `triangulation/schemas/triangulation.v1.json` | Canonical runtime copy |

## 2. Code Artifacts

- `triangulation/__init__.py`, `triangulation/__main__.py` — CLI entrypoint
- `triangulation/correlate.py` — correlation engine
- `triangulation/bridge_map.json` — GOV-CI-03 ↔ fd_flow bridge rules
- `.github/scripts/check-triangulation-governance.py` — governance gate

## 3. Tests

- `tests/test_triangulation.py` — fixture correlation, proven edge assertion, partial source handling, launch_blocked preservation

## 4. Fixtures

- `triangulation/fixtures/tri-demo-001/` — Mechanic ledger, Scorpion ledger, Slingshot frame with shared `case_id`

## 5. Gates

| Gate | Script | Sequence |
|------|--------|----------|
| `make triangulation-gate` | `.github/scripts/check-triangulation-governance.py` | pytest → correlate on `tri-demo-001` → assert proven edge |

## 6. Proof Bundle

Target: [../../proof/forensics/TRIANGULATION_V1_PROOF.md](../../proof/forensics/TRIANGULATION_V1_PROOF.md)

| Claim | Label | Evidence |
|-------|-------|----------|
| Proven invariant_overlap edge on tri-demo-001 | `proven` | Fixture replay |
| Jarvis forensic_triangulation tool route | `none_yet` | MECH-CHAT-01 deferred |
| Cross-machine replay | `none_yet` | Deferred |

## 7. Reproduction Commands

```bash
make triangulation-gate
python -m pytest tests/test_triangulation.py -q
python -m triangulation correlate --case-id tri-demo-001 --fixture tri-demo-001
```

## 8. Activation Dependencies

**Existing subsystems required:** AI Mechanic (ledger output), Scorpion (trace forensics), optional AI Slingshot (kinetic frame)

**Order among batch:** 2 of 3 — depends on Mechanic + Scorpion runtime roots being readable

**Rationale:** Triangulation reads subsystem-native ledgers; it does not replace them. Activates after Lineage Console because cross-subsystem correlation benefits from operator visibility, and before NTP because forensics lane is independent of creative pipeline.
