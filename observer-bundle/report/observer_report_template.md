# Observer Verification Report — CP-001

**Observer ID:** ____________________  
**Date (UTC):** ____________________  
**Environment:** ____________________ (OS, Python version)

## Package under test

| Field | Value |
|-------|-------|
| Package ID | BK-PKG-1 |
| Chain ID | CHAIN-BK-1 |
| Designation | CP-001 |
| Expected canonical hash | `b1d4f5a5c9a5e7d8565617aadd6240213664bd624120ba31dce290fbeba53f52` |

## Commands executed

```bash
python bone_king_reproduce.py BK-PKG-1.json
python continuity_verify.py BK-PKG-1.json
```

## Results

| Check | Pass / Fail | Notes |
|-------|-------------|-------|
| RP-1.0 reproduction | | |
| Event hash match | | |
| Replay state match | | |
| Claim verified by replay | | |
| Canonical hash match | | |

## Output captured

```text
(paste output of continuity_verify.py here)
```

## Final determination

- [ ] **VERIFIED** — All checks passed; canonical hash matches.
- [ ] **FAILED** — Describe discrepancy below.

**Observer signature / ID:** ____________________

**Comments:**

---

*This report confirms Category B reproduction per RP-1.0. No founder dependencies were required.*
