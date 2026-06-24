# Mission #004 — Calibration Preservation

**Status:** Implemented (CE-1, CLG-1, C-PoLT, Continuity Graph v2)

## Objective

Preserve corrigibility — the moments where reality successfully changed judgment — as first-class, reconstructible, transmissible artifacts.

## Constitutional grounding

| Document | Role |
|----------|------|
| [K_INFINITY_CONSTITUTIONAL_COMMENTARY.md](../continuity-os/K_INFINITY_CONSTITUTIONAL_COMMENTARY.md) | Why K-∞ governs the stack |
| [CALIBRATION_LAYER_SPECIFICATION.md](../continuity-os/CALIBRATION_LAYER_SPECIFICATION.md) | C0–C5 invariants, F1–F5 functions |
| [CK1_CONTINUITY_KERNEL.md](../continuity-os/CK1_CONTINUITY_KERNEL.md) | CK-5, CK-6 minimal requirements |

## Implementation map

| Phase | Module | Deliverable |
|-------|--------|-------------|
| Objects | `calibration_objects.py` | ExpectationObject … CalibrationEvent |
| Engine | `correction_engine_ce1.py` | CE-1 F1–F5 pipeline |
| Lineage | `calibration_lineage_graph.py` | CLG-1 with Q1–Q4 queries |
| Graph | `continuity_graph_v2.py` | Wire graph + calibration layer |
| Pipeline | `calibration_pipeline.py` | MVCD + C-PoLT (7 tests) |
| Receipt | `correction_object.py` | CorrectionObject + CRR-1 |

## Verification

```bash
uv run pytest tests/crk1/test_mission_004_calibration.py -q
uv run python -c "from src.crk1.calibration_pipeline import run_continuity_proof_of_life; r,t=run_continuity_proof_of_life(); print(t.overall)"
```

## C-PoLT (Continuity Proof-of-Life Test)

Seven tests proving end-to-end calibration:

1. Expectation recorded
2. Reality contact (evidence + hash)
3. Contradiction detected
4. Surprise quantified
5. Correction applied
6. CRR-1 preserved
7. Future steward reconstruction

## Next steps

- Wire CE-1 into governance runtime decision loop
- DARZ-VR CalibrationEvent node prefabs (M4 in roadmap)
- Cross-link GRR-1 ↔ CRR-1 in production receipts
