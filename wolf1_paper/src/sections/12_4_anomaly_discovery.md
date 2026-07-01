## 12.4 Anomaly Discovery Framework

Diagram reference: `assets/diagrams/anomaly_discovery_framework.mmd`

WOLF‑1 includes a subsystem for detecting **unknown‑unknowns** — behaviors not covered by invariants or fault codes.

---

### 12.4.1 Multi‑Channel Detection

Anomalies are detected across:

- telemetry patterns
- power/thermal gradients
- LLM output distributions
- invariant evaluation timing
- epistemic metrics
- drift signatures

---

### 12.4.2 Baseline Models

WOLF‑1 maintains baseline statistical models for:

- normal telemetry
- normal cognitive behavior
- normal invariant evaluation patterns

These baselines are updated only with ground authorization.

---

### 12.4.3 Anomaly Classes

| Class | Description |
|--------|-------------|
| **A0** | Benign anomaly |
| **A1** | Behavioral drift |
| **A2** | Subsystem divergence |
| **A3** | Constitutional risk |

A2 and A3 escalate automatically to ground.

---

### 12.4.4 Anomaly Receipts

Each anomaly generates a receipt containing:

- anomaly type
- anomaly score
- affected subsystems
- contributing signals
- recommended actions

Anomaly receipts are stored alongside cognitive receipts.

---
