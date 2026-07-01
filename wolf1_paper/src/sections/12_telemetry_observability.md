# 12. Telemetry, Observability, and Ground Interface

WOLF‑1 exposes a comprehensive observability surface for ground operators.

---

## 12.1 Telemetry Channels

- PowerState
- PropulsionState
- ThermalState
- FaultJournal
- RunLedger summaries
- Mode transitions
- Epistemic metrics

Telemetry is **read‑only** to cognitive tenants.

---

## 12.2 Observability Guarantees

- Every cognitive run produces a receipt.
- Every fault produces a fault record.
- Every invariant evaluation produces a meta‑receipt.
- All receipts are cryptographically signed.
- All logs are checksummed and redundant.

---

## 12.3 Ground Interface

Ground receives:

- proposals
- receipts
- fault summaries
- power/thermal context
- safe‑mode status
- anomaly reports

Ground may:

- approve/reject proposals
- authorize safe‑mode exit
- update policies
- update invariants (via Section 14 protocol)

---
