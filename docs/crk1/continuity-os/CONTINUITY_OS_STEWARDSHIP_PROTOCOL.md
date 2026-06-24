# Continuity OS — Stewardship Protocol

**Version:** 1.0  
**Status:** Normative

---

## 1. Steward admission

### 1.1 SCT evaluation

Run **Stewardship Calibration Test (SCT)** across:

- R-contact (active reality channels)
- Contradiction sensitivity
- Correction responsiveness
- Calibration gain
- Drift resistance
- Transferability

### 1.2 Threshold check

Require:

\[
C(t) > C_{\min} \quad \text{and} \quad RAI > RAI_{\min}
\]

### 1.3 Registration

Add steward to **Stewardship Registry (SR)** with:

- `steward_id`
- `role`
- `authority_scope`
- `lineage_refs`
- `SCT_scores`

---

## 2. Steward operation

### Obligations

| ID | Obligation |
|----|------------|
| O1 | Maintain active reality contact |
| O2 | Record decisions (GRR-1) and calibrations (CRR-1) |
| O3 | Submit to periodic SCT re-evaluation |
| O4 | Participate in challenge and review under CRK-1 (K8, KΩ) |

### Governed actions

All constitutional mutations pass through `CRK1GovernanceEngine.commit_action()` with governance receipt.

---

## 3. Steward handoff

### 3.1 Pre-handoff — SHP-Packet

Generate **Stewardship Handoff Packet** containing:

- Key GRR-1s
- Key CRR-1s
- CLG-1 slice (calibration lineage for tenure)
- Drift map (CE/SE/RAI/RDI trajectory)
- Current invariant state

### 3.2 Successor SCT

Evaluate successor's SCT; require non-zero corrigibility (\(C > 0\)).

### 3.3 Continuity check

Successor must be able to reconstruct:

- **Why** past judgments were made (GRR-1)
- **Where** reality changed them (CRR-1)

### 3.4 Authority transfer

1. Update Stewardship Registry
2. Log handoff as **StewardshipEvent** in CLG-1
3. Issue governance receipt for transfer action

---

## 4. External steward reproduction (Mission #003)

Non-founder stewards may certify runtime reproduction:

1. Rebuild from `RP-CRK1-v1.0`
2. Pass harness (see [MISSION-003-OPERATOR-MANUAL.md](../mission-003/MISSION-003-OPERATOR-MANUAL.md))
3. Issue D-3 Seal with `oral_tradition_used: false`

This is the highest form of stewardship verification for CRK-1 v1.0.

---

## 5. Failure

Stewardship breakdown (Type V collapse) occurs when stewards fail SCT but authority persists. See [CONTINUITY_COLLAPSE_TAXONOMY.md](CONTINUITY_COLLAPSE_TAXONOMY.md).
