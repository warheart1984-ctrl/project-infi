# Proof of Life Demo Script

**First public demonstration** — CRK-1 as a running constitutional runtime.

Record this sequence once Continuity API v0.1 and CRK-Explorer Phase 2 are wired.

---

## Prerequisites

- CRK-1 runtime running with `CRK1GovernanceEngine` active
- Continuity API v0.1 serving truth boundary objects
- CRK-Explorer connected (`LIVE` in header)
- (Optional Phase 4+) DARZ-VR subscribed to same event stream

---

## Demo sequence

### Step 1 — Create identity

```
POST /identity
```

- CRK-1 issues Identity + governance receipt
- CRK-Explorer: new Identity node (fade-in)
- VR (later): spatial node in IdentityLayer

### Step 2 — Create decision

```
POST /decision
```

- Decision node appears, linked to Identity (`initiated_by`)
- Receipt issued and anchored to Merkle spine

### Step 3 — Generate outcome

```
POST /outcome
```

- Outcome node linked to Decision (`results_in`)
- Receipt issued

### Step 4 — Attach evidence

```
POST /evidence
```

- Evidence node linked to Outcome (`documented_by`)
- Receipt issued

### Step 5 — Add interpretation

```
POST /interpretation
```

- Interpretation node linked to Evidence (`interpreted_by`)
- Receipt issued
- Graph updates live via `WS /events/stream`

### Step 6 — Inspect provenance

In CRK-Explorer, click any node:

- Object ID
- Receipt ID
- Provenance parents/children
- Full continuity chain tab

### Step 7 — Live updates

Trigger a new interpretation → watch graph update in real time (footer ticker + center pane).

### Step 8 — (Optional) VR renderer

Unity DARZ-VR shows the same graph spatially; click node → receipt panel.

---

## Success condition

A complete continuity chain is created, visualized, inspected, and updated live:

```
Identity → Decision → Outcome → Evidence → Interpretation
```

Each step has a governance receipt. Merkle root advances. No client invented synthetic nodes.

---

## Automated rehearsal (today)

Until API + Explorer ship, partial proof exists in tests:

```bash
python -m pytest tests/crk1/test_governance_engine.py tests/crk1/test_crk1_governance_engine.py -q
```

Chain: propose → ratify / amend with receipt verification + Merkle anchor.

---

## Recording checklist

- [ ] Header shows `CRK-1 v1.0` and `LIVE`
- [ ] Breadcrumb reflects focus chain
- [ ] Each POST shows receipt in inspector
- [ ] Invariant layers K0_K2, K3_K6, K7_K12 = PASS on receipts
- [ ] CE_after ≥ CE_before, SE_after ≥ SE_before on each receipt
- [ ] Merkle root changes after each governed action
