# CRK-1 Minimal Runtime RFC

**Status:** Normative (v1.0)  
**Audience:** External stewards, integrators, Mission #003 operators  
**Scope:** Minimum surface required to claim a CRK-1-compatible runtime

---

## 1. Purpose

CRK-1 is a **constitutional runtime** whose sole mandated purpose is to preserve the capacity of future stewards to be recalibrated by reality (K-∞). See [CRK1_CONSTITUTIONAL_PREAMBLE.md](continuity-os/CRK1_CONSTITUTIONAL_PREAMBLE.md).

This RFC defines the **minimum implementable boundary**: objects, invariants, governance gate, receipts, and verification hooks required for founder-independent reproduction.

---

## 2. Normative references

| Artifact | Location |
|----------|----------|
| Kernel invariants K0–K15, KΩ | `docs/crk1/crk1_invariants.yaml`, `CRK-1-UNIFIED-KERNEL-SPECIFICATION.md` |
| K-∞ Prime Directive | `docs/crk1/continuity-os/K_INFINITY_PRIME_DIRECTIVE.md` |
| Governance receipt header | `fixtures/crk1/governance_receipt_header.schema.json` |
| D-3 Reproduction Seal | `fixtures/crk1/reproduction_seal.schema.json` |
| CRR-1 Calibration receipt | `fixtures/crk1/calibration_reconstruction_receipt.schema.json` |
| Reproduction packet | `fixtures/crk1/reproduction_packet.schema.json` |
| Reference implementation | `src/crk1/` |

---

## 3. Runtime identity

A conforming runtime MUST expose:

```
runtime_id     : stable identifier (e.g. "CRK-1")
runtime_version: semver string (e.g. "1.0.0")
epoch          : monotonic kernel epoch (integer)
merkle_root    : hash over anchored governance receipts (hex)
```

Initialization MUST produce a valid `CRK1Runtime` (or equivalent) with empty or genesis ledgers and `epoch ≥ 0`.

---

## 4. Core object model (minimum)

Wire schemas live under `fixtures/crk1/v01/` and `fixtures/crk1/*_object.schema.json`.

| Object | Required fields (minimum) | Role |
|--------|---------------------------|------|
| **Identity** | `id`, provenance | Actor in continuity graph |
| **Evidence** | `id`, `timestamp`, payload hash | Reality contact artifact |
| **Decision** | `id`, `identity_id`, inputs | Governed judgment act |
| **Outcome** | `id`, `decision_id`, effects | Consequence of decision |
| **Interpretation** | `id`, plural hypotheses | Semantic layer (K7–K12) |
| **GovernanceReceiptHeader** | per schema | Proof of governed action |
| **GRR-1** | per `governance_reconstruction_receipt.schema.json` | Why a decision was made |
| **CRR-1** | per `calibration_reconstruction_receipt.schema.json` | Where reality changed judgment |

Continuity graph edges: Identity → Decision → Outcome → Evidence → Interpretation (append-only DAG).

---

## 5. Constitutional kernel (minimum)

The runtime MUST enforce, at minimum:

- **K-∞** — non-zero corrigibility; reality access; calibration preservation
- **K0–K2** — consequence transmission (decision → outcome → evidence)
- **K3–K6** — preservation (no exposure reduction on valid transitions)
- **K7–K12** — assimilation (semantic pluralism, anti-monoculture)
- **KΩ** — kernel challenge path (consequence-exposed evolution)

Drift metrics **CE**, **SE**, **RAI**, **RDI**, **CFE** MUST be computable from runtime state.

---

## 6. Governance gate (normative commit order)

No constitutional mutation MAY occur without a valid governance receipt.

```
commit_action(action, receipt):
  1. verify(receipt)           # schema + invariants + drift + red-team
  2. anchor(receipt)           # index + Merkle spine
  3. apply_action(action)      # state mutation ONLY here
```

Implementations MUST refuse commits when verification fails and MUST emit refusal context in the receipt or error envelope.

Reference: `src/crk1/crk1_governance_engine.py`, `src/crk1/governance_engine.py`.

---

## 7. Continuity API (minimum surface)

Until the full Continuity API v0.1 ships, a minimal runtime MUST support programmatic access equivalent to:

| Operation | Semantics |
|-----------|-----------|
| `create_evidence(...)` | Append evidence node |
| `record_decision(...)` | Governed decision with receipt |
| `record_outcome(...)` | Bind outcome to decision |
| `get_merkle_root()` | Current audit spine root |
| `verify_receipt(receipt)` | Constitutional verification |
| `run_invariant_suite()` | K0–K12 executable checks |

Full REST/WS contract: `docs/crk1/roadmap/CONTINUITY_API_V0_1.md`.

---

## 8. Reproduction boundary

A runtime is **reproducible** iff an external steward can:

1. Rebuild from `RP-CRK1-v1.0` without founder oral tradition
2. Pass Mission #003 harness suites (see `MISSION-003-REPRODUCTION-CHECKLIST.md`)
3. Issue a `ReproductionSeal` with `oral_tradition_used: false` and `results.all_passed: true`

The D-3 Seal is a **receipt**, not a badge. Schema: `fixtures/crk1/reproduction_seal.schema.json`.

---

## 9. Non-goals (v1.0)

- UI (CRK-Explorer, DARZ-VR) — specified, not required for RFC compliance
- Full Continuity API deployment — specified in roadmap
- CRR-1 / CLG-1 runtime builders — schema normative; implementation optional for minimal RFC

---

## 10. Compliance statement

An implementation MAY claim **CRK-1 v1.0 RFC compliance** when:

- [ ] All §4 objects validate against wire schemas
- [ ] §5 invariants are enforced on every governed transition
- [ ] §6 commit order is never violated
- [ ] Mission #003 checklist passes in a clean environment
- [ ] D-3 Seal can be issued with all `tests_executed` fields `PASS`

**Operator procedure:** `docs/crk1/mission-003/MISSION-003-OPERATOR-MANUAL.md`  
**Runnable checklist:** `docs/crk1/mission-003/MISSION-003-REPRODUCTION-CHECKLIST.md`
