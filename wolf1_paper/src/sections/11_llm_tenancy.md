# 11. LLM Tenancy and Tool Governance

WOLF‑1 hosts one or more LLM tenants inside a strictly governed sandbox.
LLMs are **never** granted direct system access; all interactions are mediated through CAS.

---

## 11.1 Tenancy Model

- Multiple LLMs may be loaded (general + domain‑tuned).
- Only one LLM is active per run.
- All LLMs operate under the same invariant set.
- Model updates require signed, audited, ledger‑recorded authorization.

---

## 11.2 Tool Governance

Tools available to LLMs are:

- identity‑scoped
- capability‑scoped
- invariant‑checked
- read‑only unless explicitly permitted

Examples:

| Tool | Permission | Notes |
|------|------------|--------|
| Telemetry Reader | Read‑only | Enforced by INV.DATA.TELEMETRY_READ_ONLY |
| Planner | Proposal‑only | Enforced by INV.PLAN.PROPOSAL_ONLY |
| Simulation | Sandboxed | No actuator access |
| File Access | Read‑only | No mutation of canonical logs |

---

## 11.3 LLM Output Mediation

CRK‑1 post‑invariant evaluation ensures:

- actuator commands stripped
- proposals downgraded
- telemetry mutations blocked
- unsafe patterns flagged

Epistemic receipts (Section 6.4) provide correctness signals.

---
