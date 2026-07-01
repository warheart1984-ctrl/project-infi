# 1. Mission Context and Design Philosophy

WOLF‑1 is a free‑flying governed compute node designed for long‑duration autonomous operation in high Earth orbit or at a Lagrange point. Its mission is to provide resilient, governed cognitive capability under extreme latency, radiation, and thermal constraints.

### Core Principle
**Governance is non‑optional. Cognition is optional.**
The node must survive without LLMs. It must not operate without CRK‑1.

### Mission Profile

| Field | Value |
|-------|--------|
| Mission Type | Free‑flying governed compute node |
| Design Life | Decades, minimal servicing |
| Failure Doctrine | Fail safe, not fail silent |
| LLM Role | Advisor, planner, analyst — never final authority |
| Use Cases | On‑orbit analysis, mission planning, high‑latency operator copilots, autonomous health monitoring |

### Key Constraints

- High latency / intermittent connectivity
- Radiation‑hardened compute required
- No‑touch maintenance
- Strong auditability
- Fault isolation between cognition and hardware

---
