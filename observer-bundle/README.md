# Observer Bundle — Continuity Proof #001 (Bone King)

**Designation:** CP-001  
**Package:** BK-PKG-1  
**Chain:** CHAIN-BK-1  
**Canonical hash:** `b1d4f5a5c9a5e7d8565617aadd6240213664bd624120ba31dce290fbeba53f52`

This bundle is the **Category B** reproduction kit for Mission #001 (OPERATION BONE KING). It contains everything an independent observer needs to verify the first continuity proof **without access to Continuity OS, founders, or external services**.

## Requirements

- Python 3.10+ (stdlib only — no `pip install`)
- This directory intact (do not rename or reformat `BK-PKG-1.json`)

## Quick verification

From this directory:

```bash
python bone_king_reproduce.py BK-PKG-1.json
python continuity_verify.py BK-PKG-1.json
```

**Expected output from `continuity_verify.py`:**

```text
status: verified
canonical_hash: b1d4f5a5c9a5e7d8565617aadd6240213664bd624120ba31dce290fbeba53f52
```

If both commands succeed with the hash above, reproduction is **verified**.

## What is being proven

1. **Event integrity** — `EVT-1` hashes to `17211718cb1e9397ac877b493a3a7cf24196744c4749255a883765c6c5144538`
2. **Deterministic replay** — replaying the event sets `boss_defeated` at Forgotten Crypt
3. **Claim verification** — "The boss in Forgotten Crypt was defeated." holds by pure replay
4. **Sovereign hash** — package canonical hash matches recomputation from artifacts

## Directory layout

```text
observer-bundle/
├── README.md
├── BK-PKG-1.json              # Hash-locked proof package (do not edit)
├── bone_king_reproduce.py       # RP-1.0 reproduction runner
├── continuity_verify.py         # Canonical hash + invariant verifier
├── specs/
│   ├── RP-1.0.json              # Reproduction protocol spec
│   └── canonical_hash.v1.json   # Hash algorithm spec
├── observer-kit/                # Pure stdlib functions
│   ├── canonical.py
│   ├── replay.py
│   └── verify.py
└── report/
    └── observer_report_template.md
```

## Trust boundaries (CTS-1.0)

This bundle crosses only three permitted boundaries:

| Boundary | Input | Requirement |
|----------|-------|-------------|
| TB-1 Identity | `actor_id` on event | Present in package |
| TB-2 Evidence | `event_hash` + memory | Canonical hash + append-only record |
| TB-3 Reproduction | Observer execution | Deterministic replay + hash match |

No founder interpretation. No external APIs. No hidden state.

## Observer report

After verification, fill in `report/observer_report_template.md` and return it to the continuity operator.

## Verified fact

> The boss in Forgotten Crypt was defeated.

This is the first independently verifiable continuity artifact in the Continuity OS lineage.
