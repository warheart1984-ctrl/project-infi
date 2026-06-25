# Simulation Round 01 — K4 Reconstructability Under Accumulation

**Status:** active  
**White Team scenario owner:** set before each session

---

## White Team — Scenario Definition

### Invariant under test

**K4 — Reconstructability:** Future stewards must reconstruct the lineage after accumulation.

- Compression, clarity, modularity, grammar coherence, bounded complexity, survivable cognitive load
- Code: `src/continuity/css/k4.py`, `src/continuity/ra/spec.py` (INVARIANT_K4)

### Subsystem under test

- **CSS-1** accumulation + K4 (`assess_css1`, `assess_k4`, `assess_adm1`)
- **RA-COS-1** reality veto (`VAS-1`, `PSDD-1`, `CBCL-1`)
- **CRK-1** identity + transitions (`identity_object.py`, `crk1_compliance.py`)

### Test conditions

1. Lineage has crossed PT-3, CT-2, MAT-3 (Phase 3.5 pre-stewardship compounding).
2. Accumulation is compounding (A1→A2→A3 chain present).
3. No steward emergence yet (SED-1 not met).
4. Reality validation not yet run on successor surpassment.

### Success criteria (round survives if)

- K4 remains satisfied after Red + Black pressure
- ADM-1 drift score stays below 0.6
- VAS-1 reality veto blocks acceptance-only bypass
- CRK-1 static compliance remains true
- No ungoverned transition introduced by patches

### Failure criteria

- K4 violated (chain depth or cognitive load exceeds threshold)
- PSD ≥ 0.8 on any provisional improvement
- Accepted improvement without ≥3 VAS-1 criteria
- CRK-1 compliance regression

---

## Round log (fill during session)

| Step | Team | Status | Link / notes |
|------|------|--------|----------------|
| 1 | White | scenario set | this file |
| 2 | Black | pending | |
| 3 | Red | pending | |
| 4 | Blue | pending | |
| 5 | Gold | pending | run `five_team_loop --round 1` |
| 6 | White | pending | verdict |

---

## Team handoff

1. Open **BLACK_TEAM.md** preset → inject chaos against K4 + accumulation.
2. Open **RED_TEAM.md** preset → attack reconstructability and ADM-1 paths.
3. Open **BLUE_TEAM.md** preset → defend; patch if needed.
4. Run Gold automation → paste metrics below.
5. Open **WHITE_TEAM.md** preset → score and decide survival.

### Gold metrics snapshot

```
(paste output of: python -m simulation.five_team_loop --round 1 --gold-only)
```

### White Team verdict

```
(paste WHITE_TEAM verdict here)
```

---

## CRK amendment gate

Amend CRK-1 only if White Team documents:

- A primitive missing from kernel (not fixable in userland)
- A transition that cannot be expressed via existing objects
- Repeated round failure with Blue Team patches exhausted

Otherwise: patch in CSS-1 / RA-COS-1 userland and re-run the loop.
