# Continuity OS — Formal Architecture

**Version:** 1.0  
**Status:** Normative

Two complementary views: **deployment layers** (L0–L5, integration) and **functional layers** (R/C/J/Q/S/M, dynamics).

---

## 1. Deployment layers (L0–L5)

```
+--------------------------------------------------------------+
|                        Layer 0: Reality                      |
|   External consequence domains (D_i), consequence intensity  |
+--------------------------------------------------------------+

+--------------------------------------------------------------+
|            Layer 1: Reality Interface Layer (RIL)            |
|  - Evidence ingestion (normalize, hash, sign)                |
|  - Reality Access Monitor (RAI, RDI, CE, SE)                 |
|  - Reality channels registry                                 |
+--------------------------------------------------------------+

+--------------------------------------------------------------+
|                Layer 2: Continuity Runtime (CRK-1)           |
|  - Object Model (Identity, Decision, Outcome, ...)           |
|  - Constitutional Kernel (K-∞, K0–K15, KΩ)                   |
|  - Governance Engine (invariant checks, receipts)            |
|  - Continuity Graph (append-only DAG)                        |
|  - Drift & Failure Engine (CE, SE, RAI, RDI, CFE)            |
|  - Kernel Challenge Path (KΩ)                                |
+--------------------------------------------------------------+

+--------------------------------------------------------------+
|                Layer 3: Continuity API Layer                 |
|  - Object endpoints                                          |
|  - Graph endpoints                                           |
|  - Metrics endpoints                                         |
|  - Event stream (SSE/WS)                                     |
+--------------------------------------------------------------+

+--------------------------------------------------------------+
|                Layer 4: Stewardship Layer                    |
|  - Stewardship Calibration Test (SCT)                        |
|  - Reproduction Harness (Mission #003)                       |
|  - D-3 Seal issuance                                         |
|  - Stewardship Ledger                                        |
+--------------------------------------------------------------+

+--------------------------------------------------------------+
|                Layer 5: Continuity Interfaces                |
|  - CRK-Explorer (web continuity browser)                   |
|  - DARZ-VR (spatial continuity browser)                      |
|  - Operator consoles (governance, drift, challenge)           |
+--------------------------------------------------------------+
```

**Spec:** `docs/crk1/roadmap/CONTINUITY_API_V0_1.md`, `CRK_EXPLORER_UI_SPEC.md`, `DARZ_VR_UNITY_SPEC.md`

---

## 2. Functional layers (R/C/J/Q/S/M)

### L0 — Reality Layer (R-Layer)

| ID | Component |
|----|-----------|
| R1 | **External Reality** — physical, ecological, social, economic, technological environment |
| R2 | **Reality Channels** — sensors, markets, feedback loops, failures, constraints, adversaries |

### L1 — Contact & Evidence Layer (C-Layer)

| ID | Component |
|----|-----------|
| C1 | **Reality Interface Adapters (RIA)** — bind concrete channels into runtime |
| C2 | **Evidence Capture Engine (ECE)** — normalize, timestamp, sign, hash evidence |
| C3 | **Contradiction Detector (CD)** — expectations vs outcomes → contradictions |

### L2 — Judgment & Governance Layer (J-Layer)

| ID | Component |
|----|-----------|
| J1 | **Judgment Engine (JE)** — models, predictions, decisions, value tradeoffs |
| J2 | **Governance Kernel (CRK-1)** — K-∞, K0–K15, KΩ; consequence exposure; challengeability |
| J3 | **Policy & Mechanism Layer (PML)** — concrete rules, institutions, protocols |

### L3 — Continuity & Reconstruction Layer (Q-Layer)

| ID | Component |
|----|-----------|
| Q1 | **GRR-1** — "Why did we decide this?" |
| Q2 | **CRR-1** — "Where did reality change us?" |
| Q3 | **Continuity Trace Engine (CTE)** — lineage graphs, drift maps, reconstruction paths |
| Q4 | **Calibration Lineage Graph (CLG-1)** — linked calibration events across time |

### L4 — Stewardship & Transfer Layer (S-Layer)

| ID | Component |
|----|-----------|
| S1 | **Stewardship Calibration Test (SCT)** — corrigibility test for stewards |
| S2 | **Stewardship Handoff Protocol (SHP)** — transfer of authority + calibration |
| S3 | **Stewardship Registry (SR)** — identity, roles, authority, lineage |

### L5 — Meta-Continuity Layer (M-Layer)

| ID | Component |
|----|-----------|
| M1 | **Continuity Metrics Engine (CME)** — RAI, CFE, drift indices |
| M2 | **Continuity Failure Monitor (CFM)** — collapse regime detection |
| M3 | **Constitutional Update Engine (CUE)** — safe invariant evolution under K-∞ |

---

## 3. Layer mapping (deployment ↔ functional)

| Deployment | Primary functional layers |
|------------|---------------------------|
| L0 Reality | R-Layer |
| L1 RIL | C-Layer |
| L2 CRK-1 | J-Layer + Q-Layer (runtime core) |
| L3 API | Exposes J, Q, M |
| L4 Stewardship | S-Layer + Mission #003 |
| L5 Interfaces | Read-only views over L3 |

---

## 4. Data flow (summary)

```
Reality (R) → Evidence (C) → Contradiction (C) → Correction (J)
     → CRR-1 (Q) → CLG-1 (Q)
Decision (J) → Outcome → GRR-1 (Q)
Governance receipts → Merkle spine → D-3 Seal (S)
Metrics (M) → CFM → collapse alerts
```

See: [CONTINUITY_OS_RUNTIME_SPEC.md](CONTINUITY_OS_RUNTIME_SPEC.md), [CRK1_GRAPH_DATA_CONTRACT.md](../roadmap/CRK1_GRAPH_DATA_CONTRACT.md)
