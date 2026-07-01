# 6. Formal Sequence Diagram

The sequence diagram defines the full lifecycle of a governed cognitive run.

Diagram reference: `assets/diagrams/sequence_diagram.mmd`

---

## 6.1 Actor Definitions

| Actor | Description |
|--------|-------------|
| **GND** | Ground operator |
| **W1** | WOLF‑1 node |
| **PWR** | Power subsystem |
| **CAS** | Constitutional API layer |
| **CRK** | Invariant engine |
| **LLM** | Sandboxed cognitive tenant |
| **LEDGER** | RunLedger + FaultJournal |

---

## 6.2 Sequence Flow (Narrative)

### 1. Identity & Admission
Ground submits request with identity + intent.
INV.ID.ROLE_BOUND and INV.ID.CAPABILITY_SCOPE enforced.

### 2. Power Pre‑Check
W1 queries PowerState.
If failsafe floor unavailable → SAFE‑MODE.

### 3. CAS Run Admission
CAS opens candidate run.

### 4. Pre‑Invariant Evaluation
CRK‑1 evaluates identity, capability, power, safe‑mode, data rules.

### 5. Sandboxed LLM Invocation
LLM receives read‑only telemetry and allowed tools.

### 6. Post‑Invariant Evaluation
CRK‑1 strips actuator commands, enforces proposal‑only, blocks telemetry mutation.

### 7. Receipt & Ledger
CAS writes receipt with spans, hashes, power context, faults.

### 8. Response to Ground
Ground receives proposals + receipt summary.

---
