# Constitutional Risk Runtime — Governed Forecast Layer

**Class:** Constitutional Contract (forecast layer above Constitutional State)

## Purpose

The Constitutional Risk Runtime answers:

> Given receipts and constitutional state, what is likely to go wrong next, and where?

It is **not binding law**. It is a governed forecaster that:

- Never mutates legal state directly (no `apply_transition`)
- Emits `RiskReceiptV2` observations
- Stores forecast `ConstitutionalRiskState` objects as domain documents
- Provides early-warning signals for Amendment, Institutional, and Operator runtimes

**Stack position:**

```
Constitution → Contract → Receipt → State Machine → Constitutional State → Constitutional Risk
```

**Implementation:** `constitutional_substrate/risk_runtime.py`  
**Receipt type:** `RiskReceiptV2` in `constitutional_substrate/receipts_v2.py`  
**TypeScript:** `aaes-os/packages/governed-memory/src/receipts_v2.ts`

---

## Risk object (`constitutional_risk`)

```json
{
  "state_id": "risk__truthruntime__no_truth_without_verification__2026-06-23T08:00:00Z",
  "state_type": "constitutional_risk",
  "scope": {
    "runtime": "TruthRuntime",
    "invariant": "NO_TRUTH_WITHOUT_VERIFICATION"
  },
  "snapshot_at": "2026-06-23T08:00:00Z",
  "risk_score": 0.73,
  "risk_factors": [
    {"factor": "unresolved_divergences", "weight": 0.2, "value": 4},
    {"factor": "overdue_remediations", "weight": 0.4, "value": 2}
  ],
  "predicted_failures": [
    {
      "type": "amendment_required",
      "invariant": "NO_TRUTH_WITHOUT_VERIFICATION",
      "probability": 0.72,
      "horizon": "7d"
    }
  ],
  "recommended_actions": [
    {
      "type": "initiate_amendment_analysis",
      "target": "TruthRuntime",
      "urgency": "high"
    }
  ]
}
```

---

## Risk receipt (`RiskReceiptV2`)

| Field | Value |
|-------|--------|
| `runtime` | `ConstitutionalRiskRuntime` |
| `action_type` | `constitutional_risk_forecast` |
| `lifecycle.stage` | `observation` |
| `invariant.name` | `SYSTEM_MUST_FORECAST_CONSTITUTIONAL_FAILURES_FROM_EVIDENCE` |
| `constitutional_risk` | Payload: score, scope, factors, predictions, actions |

Risk receipts are **governed hints** — visible, auditable, replayable. Amendment Runtime may require acknowledgment or explicit dismissal (with receipts) for high-risk `amendment_required` predictions.

---

## Inputs (no invented data)

| Source | Signals |
|--------|---------|
| Receipt stream | Divergence frequency per invariant/runtime, remediation latency, arbitration frequency, observer challenges |
| Constitutional state | `health_score` / `debt_score` trajectory, `runtime_compliance`, `invariants_under_stress` |

Key derived signals (v0):

- **Trend** — health/debt slope from constitutional state observation receipts
- **Acceleration** — divergences increasing in second half vs first half of lookback window
- **Concentration** — failures clustered by runtime + invariant scope
- **Latency** — remediations past SLA without closure

Default lookback: **30 days**. Forecast horizon: **7d**.

---

## Scoring (v0 — deterministic, no ML)

Per scope `(runtime, invariant)`:

| Symbol | Meaning |
|--------|---------|
| D_t | Divergences in lookback window |
| O_t | Overdue remediations (SLA = 7 days, no closure receipt) |
| A_t | Arbitrations in window |
| H_t | Health score slope (only downward slope contributes) |

Normalized:

- d = min(1, D_t / 10)
- o = min(1, O_t / 5)
- a = min(1, A_t / 5)
- h = max(0, −H_t)

```
risk_score = 0.2·d + 0.4·o + 0.15·a + 0.25·h
```

Overdue obligations and downward health trend dominate.

---

## Predicted failures (rule-based v0)

| Condition | Prediction |
|-----------|------------|
| risk_score > 0.7 and O_t > 0 | `remediation_failure` @ 7d |
| risk_score > 0.8 and D_t increasing | `amendment_required` @ 7d |
| risk_score > 0.9 and A_t ≥ 2 | `governance_breakdown` @ 7d |

Probability: `clamp(0.1 + 0.85 × risk_score, 0, 1)`.

---

## Integration points

| Runtime | Use |
|---------|-----|
| **Amendment** | Soft trigger on `amendment_required` — must acknowledge or dismiss with receipt |
| **Institutional** | Prioritize governance work by risk score |
| **Operator / AAIS / URG** | Surface scope risk in consoles |
| **Governance Gate** | After boot: `refresh_constitutional_risk_forecasts()`; optional future: refuse boot when global risk exceeds threshold without mitigation plan |

---

## API

```python
from constitutional.runtime import ConstitutionalStateRuntime, ConstitutionalRiskRuntime

csr = ConstitutionalStateRuntime()
risk_rt = ConstitutionalRiskRuntime(csr)

forecasts = risk_rt.forecast()
receipts = risk_rt.forecast_and_emit()
```

Boot path (automatic after constitutional state refresh):

```python
from constitutional.runtime.risk_runtime import refresh_constitutional_risk_forecasts
refresh_constitutional_risk_forecasts()
```

---

## Invariants (CR-1..CR-4)

| ID | Rule |
|----|------|
| CR-1 | Risk runtime never calls `apply_transition` |
| CR-2 | Every forecast emits a complete `RiskReceiptV2` |
| CR-3 | `risk_score` is deterministic from receipt stream + constitutional state |
| CR-4 | Forecasts are observations only — impact boundary excludes execution and state mutation |
