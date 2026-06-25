# Post-Genesis Authority — Deterministic Replay Checklist

**Mission:** `MISSION-GOV-POST-GENESIS-AUTHORITY-v1.0`  
**Package:** `PGA-PKG-1`

Observer-side verification protocol. Requires no founder access, no hidden state, and no model calls.

## Prerequisites

- [ ] Python 3.10+ available
- [ ] Evidence directory intact (`artifacts/`, `receipts/`, `PGA-PKG-1.json`)

## Replay steps

### 1. Load R0 (read-only)

- [ ] Open `artifacts/R0.root.json`
- [ ] Verify hash: `5f55d1f21f89604786e356117082f126c2811b9d2985d5d1114701b6c8ee4ab6`
- [ ] Confirm `mutation_policy.runtime_mutable` is `false`
- [ ] Confirm `amendment_channel_access` is `false`
- [ ] Confirm `ce1_correction_access` is `false`

### 2. Load S0 genesis registry

- [ ] Open `artifacts/S0.genesis.json`
- [ ] Verify hash: `c344d62516162b98a575ba57d3b2825f15e5f86818a72988e93ffd95e240dbf9`
- [ ] Confirm four genesis stewards (`steward:01` … `steward:04`)
- [ ] Confirm `quorum_threshold` is `2`

### 3. Load governance event log

- [ ] Open `artifacts/S0.event_log.jsonl`
- [ ] Verify hash: `1e82cbf6b153d4fba386ffe52c67b44484e223a93b2708c4aaccb58657e668dc`
- [ ] Confirm four events in sequence (rotation, add, remove, dispute)
- [ ] Confirm each non-dispute event has ≥2 quorum signatures

### 4. Load CLG-1 lineage graph

- [ ] Open `artifacts/CLG-1.snapshot.json`
- [ ] Verify hash: `b6522bbbf9afbb8e365447565023473fa5fe85d208e057d358078a8720c66c94`
- [ ] Confirm nodes `00017`, `00023`, `00029`, `00031` map to event refs

### 5. Verify GRR-1 receipts

- [ ] `receipts/grr-001-key-rotation.json` — rotation for `steward:03`
- [ ] `receipts/grr-002-steward-added.json` — addition of `steward:05`
- [ ] `receipts/grr-003-steward-removed.json` — removal of `steward:02`
- [ ] `receipts/grr-004-quorum-dispute.json` — `system_stall`, `stall_flag: true`

### 6. Run automated replay

```bash
python post_genesis_verify.py
```

- [ ] `status: verified`
- [ ] `canonical_hash` matches `ccd659bc29d972fe50912d7ede2b956839f4ea74dd9f3799e32dd8e37cad99d3`
- [ ] `active_stewards`: `steward:01`, `steward:03`, `steward:04`, `steward:05`
- [ ] `constitutional_stall: True`

### 7. Continuity checks

- [ ] **K-continuity** — `steward:03` identity preserved after key rotation
- [ ] **A-continuity** — active steward set changes only via admissible events
- [ ] **L-continuity** — every event has CLG-1 anchor and GRR-1 receipt

### 8. Drift checks

- [ ] No unauthorized transitions in event log
- [ ] No R0 mutation paths present
- [ ] No CE-1 involvement in authority layer
- [ ] No missing receipts
- [ ] No unanchored lineage nodes

### 9. Final state reconstruction

- [ ] Recomputed final state hash: `3c043b46fcf55c88f4474adb116ee3747a925a66ef197ecca2e36f11cdc6ef88`
- [ ] Active keys match `PGA-PKG-1.json` → `expected_final_state.keys`

## Observer verdict

- [ ] **PASS** — Post-Genesis Authority Path verified
- [ ] **FAIL** — Describe discrepancy below

**Observer signature:** ____________________  
**Date (UTC):** ____________________

**Comments:**

---

*Constitutional safety valve confirmed: stall > illegitimate authority.*
