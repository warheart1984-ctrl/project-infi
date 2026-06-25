# AAES-OS Network Graph

Who sits where, why, and how they interlock.

## Top-Level Structure

```
                +-------------------------------+
                |     Constitutional Layer      |
                |   (Governance & Invariants)   |
                +-------------------------------+
                         /           \
                        /             \
                       v               v
         +-------------------+     +-------------------+
         |   Architecture    |     |   Runtime Layer   |
         |    (CRK-1)        |     |  (Execution)      |
         +-------------------+     +-------------------+
                       \               /
                        \             /
                         v           v
                +-------------------------------+
                |     Implementation Layer      |
                |   (SDK, APIs, Production)     |
                +-------------------------------+
```

## Constitutional Layer (Governance / Invariants)

**Purpose:** Define legitimacy, admissibility, reconstruction, readiness, and political-economic constraints.

| Steward | Domain | Why They Sit Here |
|---------|--------|-------------------|
| Wendy | Emotional Governance (ESAF) | Ensures human-emotional admissibility and safety |
| Sue | Human Readiness Architecture | Ensures human-system alignment and readiness |
| Nishant | Accountable Reconstruction & Continuity | Ensures reconstruction is legitimate and traceable |
| Frank | Legitimacy & Admissibility | Ensures decisions meet constitutional admissibility |
| Maher | Political Economy & Decision Architecture | Ensures governance is incentive-compatible and stable |

**Interlock:** They define what is allowed, what is legitimate, and what must be proven.

## Architecture / Runtime Layer (CRK-1 / Deterministic Execution)

**Purpose:** Define the kernel, invariants, type system, and deterministic runtime.

| Steward | Domain | Why They Sit Here |
|---------|--------|-------------------|
| You | Kernel architecture, invariants, continuity substrate | Defines the substrate itself |
| William J. Storey | Claude Architect / Enterprise AI | Ensures enterprise-grade runtime patterns |
| Nirvisha | Type systems, SDKs, developer guardrails | Ensures correctness and safe extensibility |
| Nitesh | Continuity runtime, deterministic validation | Ensures runtime determinism and validation |

**Interlock:** They define how the system behaves and how invariants are enforced.

## Implementation Layer (SDK, APIs, Production Engineering)

**Purpose:** Build the tools, SDKs, APIs, and production systems that express the architecture.

| Steward | Domain | Why They Sit Here |
|---------|--------|-------------------|
| Shakeel | Backend systems | High-reliability backend execution |
| Abdullah | Frontend & UX | Human-system interaction |
| Dhaval | SDK engineering | Developer-facing tools |
| Ravi | Infrastructure | Deployment, scaling, reliability |
| Deep | Runtime integration | Ensures runtime ↔ infra coherence |
| Sachin | Production systems | Operationalization |
| Emmanuel | Data pipelines | Evidence flow & trace bus |
| Aun | API engineering | Interface stability |
| Mike | Systems integration | End-to-end integration |

**Interlock:** They define how the system is built, how it is used, and how it scales.

## Cross-Layer Flow

```
Constitutional Layer  →  defines admissibility, legitimacy, continuity claims (CDP-1)
Architecture Layer    →  CRK-1 invariants, proofs (P₁–P₄), lineage primitives
Implementation Layer  →  CEP/SDK, APIs, production trace bus
```

## Related

- [STEWARDSHIP_ROLES_CHARTER.md](./STEWARDSHIP_ROLES_CHARTER.md)
- [FIRST_WAVE_GOVERNANCE_COUNCIL.md](./FIRST_WAVE_GOVERNANCE_COUNCIL.md)
- [ARCHITECTURE_STABILIZATION_CHECKLIST.md](../architecture/ARCHITECTURE_STABILIZATION_CHECKLIST.md)
- [CDP1_CONSTITUTIONAL_SPEC.md](../../crk1/continuity/CDP1_CONSTITUTIONAL_SPEC.md)
