# Observer Verification Report — CP-GOV-001

**Observer ID:** ____________________  
**Date (UTC):** ____________________  
**Environment:** ____________________ (OS, Python version)

## Package under test

| Field | Value |
|-------|-------|
| Package ID | PGA-PKG-1 |
| Mission ID | MISSION-GOV-POST-GENESIS-AUTHORITY-v1.0 |
| Designation | CP-GOV-001 |
| Expected canonical hash | `ccd659bc29d972fe50912d7ede2b956839f4ea74dd9f3799e32dd8e37cad99d3` |

## Commands executed

```bash
python post_genesis_verify.py
```

## Results

| Check | Pass / Fail | Notes |
|-------|-------------|-------|
| R0 hash + immutability | | |
| S0 genesis hash | | |
| S0 event log hash | | |
| CLG-1 snapshot hash | | |
| GRR-1 receipt linkage | | |
| Lineage anchoring | | |
| Steward-state replay | | |
| Final state hash | | |
| Constitutional stall | | |
| Canonical hash match | | |

## Output captured

```text
(paste output of post_genesis_verify.py here)
```

## Final determination

- [ ] **VERIFIED** — All checks passed; canonical hash matches.
- [ ] **FAILED** — Describe discrepancy below.

**Observer signature / ID:** ____________________

**Comments:**

---

*Post-genesis authority verification per MISSION-GOV-POST-GENESIS-AUTHORITY-v1.0. No founder dependencies required.*
