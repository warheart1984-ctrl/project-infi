## 8.5 Graded Safe‑Mode Profiles

Diagram reference: `assets/diagrams/safe_mode_profiles.mmd`

WOLF‑1 defines four graded profiles:

### **S0 — Full Operations**
All systems nominal.

### **S1 — Cognitive Degradation**
- LLM disabled
- Planning + simulation allowed
- Telemetry full

### **S2 — Autonomy Degradation**
- LLM disabled
- Planning disabled
- Simulation limited
- Telemetry high‑cadence

### **S3 — Governance‑Only**
- Only CRK‑1 + CAS
- Only health checks
- Only safe‑pointing

Transitions:
S0 → S1 → S2 → S3
Recovery: S3 → S2 → S1 → S0

---
