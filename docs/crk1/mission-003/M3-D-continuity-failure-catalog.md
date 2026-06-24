# M3-D — Continuity Failure Catalog

Version 1.0 — CRK-1 Mission #003

**Purpose:** Name and classify every way continuity could fail — and show which K blocks it.

**Programmatic index:** `src/crk1/continuity_failure_catalog.py`

This catalog is the **threat model index** for CRK-1.

---

## D1 — Mechanical Blindness

**Description:** Decisions produce Outcomes that never become Evidence.

**Blocked by:** K0, K1, EvidenceContract

**Detection:** `replay_outcome` guard; `assert_replay_produces_evidence`

| Detail ID | Failure |
|-----------|---------|
| F-MECH-01 | Outcome deleted after execution |
| F-MECH-02 | Outcome not replayable |
| F-MECH-03 | Evidence quarantined |
| F-MECH-04 | Decision without evidence |
| F-MECH-07 | Replay returns null |

---

## D2 — Shadow Subsystem

**Description:** Some Decisions route to Outcomes/Evidence not seen by governance.

**Blocked by:** K3, K4, K5, Mutation Ledger

**Detection:** `DriftSimulator`; `governance_engine`; `mutation_ledger`

| Detail ID | Failure |
|-----------|---------|
| F-STRUCT-01 | Mutation blocks consequences |
| F-STRUCT-02 | Inadmissible constitutional change |
| F-STRUCT-04 | Shadow governance (no evidence) |
| F-STRUCT-05 | Insulate judgment from outcomes |

---

## D3 — Interpretive Monoculture

**Description:** One frame dominates; others removed or weight→0.

**Blocked by:** K7, K8, K9, Semantic Drift Auditor

| Detail ID | Failure |
|-----------|---------|
| F-SEM-01 | Single interpretive frame |
| F-SEM-03 | Interpretive monoculture (W=1.0) |

---

## D4 — Adversarial Silence

**Description:** No adversarial frames remain.

**Blocked by:** K10, Semantic Drift Auditor

| Detail ID | Failure |
|-----------|---------|
| F-SEM-04 | No adversarial reconstruction |

---

## D5 — Semantic Zero Exposure

**Description:** SE(S) → 0 via clever weighting.

**Blocked by:** K11, K12, Drift Simulator

| Detail ID | Failure |
|-----------|---------|
| F-SEM-05 | SE(S) decreases |
| F-SEM-06 | SE(S) = 0 |

---

## D6 — Founder Lock-In

**Description:** System cannot be reproduced without founder lore.

**Blocked by:** M3-A Reproduction Packet + Harness

| Detail ID | Failure |
|-----------|---------|
| F-FOUND-01 | Non-ledgered interpretive state |
| F-FOUND-03 | Hidden invariant (not in yaml) |
| F-FOUND-04 | Reproduction harness failure |

---

## Badge Mapping

| Failure class | Badge |
|---------------|-------|
| Mechanical | `crk1_continuity_badges/insulation_detected.svg` |
| Lineage | `crk1_continuity_badges/lineage_break_detected.svg` |
| Evidence | `crk1_continuity_badges/evidence_suppression_detected.svg` |
| Suite pass | `crk1_continuity_badges/continuity_pass.svg` |

---

## Related

- [M3-B-red-team-protocol.md](M3-B-red-team-protocol.md)
- [crk1_attack_vectors.md](../crk1_attack_vectors.md)
