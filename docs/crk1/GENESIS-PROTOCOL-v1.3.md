# Genesis Protocol v1.3 — Preservation → Continuity

**Version:** 1.3  
**Status:** Constitutional synthesis

## Evidence vs proof

| Layer | Question answered | Primary artifact |
|-------|-------------------|------------------|
| **Evidence** | What happened? | GRR-1, traces, packets |
| **Preservation** | Can it be reconstructed? | CRR-1, CLG-1, D-3 / R-3 seals |
| **Propagation** | Can it transfer to a new steward? | CAA-1 / CXD-1 |
| **Proof** | Is the claim machine-verifiable? | Schema validation, hash bundles, CRC invariants |

Mission #006 closes the loop from preservation to **continuity propagation**.

## Four continuity layers

```
R0 (Genesis)
  └── GRR-1 — provenance preservation (why we decided)
        └── CRR-1 — calibration preservation (where reality changed us)
              └── CLG-1 — lineage reconstruction (linked calibration graph)
                    └── CAA-1 / CXD-1 — assimilation (generational transfer)
                          └── K-∞ — corrigibility invariant (constitutional ceiling)
```

## Mission arc (M3–M6)

| Mission | Seal | Empirical? | Claim |
|---------|------|------------|-------|
| #003 | D-3 | Structural | Non-founder can rebuild the machine |
| #004 | KCR / IDC | Structural | Kernel remains adequate under challenge |
| #005 | R-3 / CLG-1 | Structural | Non-founder can reconstruct judgment lineage |
| #006 | CAA-1 | **Empirical** | New steward assimilates calibration from lineage alone |

## Genesis bundle contents (v1.3)

1. **Schemas** — `fixtures/crk1/` including `CAA1_continuity_assimilation_receipt.schema.json`
2. **Runtime** — `src/crk1/` (CRC v0.1, CAA-1, Mission #006)
3. **Observer evidence** — `nova-mission-002/observer/evidence/POST-GENESIS-AUTHORITY/`
4. **SDK harness** — `sdk/continuity-sdk/` (experiments, not API)
5. **Documentation** — `docs/crk1/mission-006/`, architecture diagram in `CONTINUITY_OS_ARCHITECTURE.md`

## Verification checklist

```bash
python -m pytest tests/mission006/ tests/crk1/test_canonical_runtime_contract.py -v
python -c "from src.crk1.mission_006_calibration_assimilation import run_mission_006_calibration_assimilation; assert run_mission_006_calibration_assimilation().passed"
```

## Related

- [MISSION-006-CONTINUITY-ASSIMILATION.md](./mission-006/MISSION-006-CONTINUITY-ASSIMILATION.md)
- [MISSION-MAP-M3-M6.md](./MISSION-MAP-M3-M6.md)
