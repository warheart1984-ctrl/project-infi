# UGR-CRK-T2 — Constitutional Boundary Detection

Class: Kernel Theorem  
Version: v0.1  
Status: Proposed (CRK-1 Complement)

Related: [UGR-CRK-T1 — Constitutional Sufficiency](UGR-CRK-T1-Constitutional-Sufficiency.md), [CRK-1](CRK-1-Constitutional-Runtime-Kernel.md)

---

## T2.1 Purpose

To define how a constitutional runtime detects when its existing kernel semantics are no longer sufficient to express emerging governance behaviors.

CRK-T2 complements CRK-T1 by providing **adaptive sufficiency** — enabling the kernel to recognize when its ontology is incomplete and an amendment may be required.

---

## T2.2 Premises

The runtime operates under CRK-1:

- Five canonical objects: Identity, Evidence, Decision, Resource, Outcome
- Four constitutional contracts: Evidence, Governance, Resource, Runtime
- Canonical transitions and replayable ledgers
- Kernel invariance (CRK-1.6)

Userland behaviors (fitness projections, cockpit panels, agents, policies) evolve over time and may reveal structural gaps in the kernel.

---

## T2.3 Theorem statement

**CRK-T2 — Constitutional Boundary Detection**

A constitutional runtime is capable of detecting its own insufficiency when recurring userland behaviors exhibit **pathological complexity**, **semantic duplication**, or **contract violation** that cannot be resolved within the existing kernel ontology.

When such patterns persist across epochs, the kernel recognizes the emergence of a missing abstraction and may initiate a constitutional amendment process.

---

## T2.4 Consequences

1. **Adaptive sufficiency:** The kernel remains minimal yet capable of self-evaluation.
2. **Amendment admissibility:** Kernel amendments become admissible only when insufficiency is empirically detected.
3. **Governance continuity:** The system evolves without arbitrary expansion or permanent stagnation.
4. **Boundary symmetry:**
   - **CRK-T1** prevents premature kernel growth.
   - **CRK-T2** prevents permanent kernel stagnation.

Together they define the dynamic constitutional perimeter.

---

## T2.5 Detection mechanism (operational sketch)

The kernel monitors **meta-signals** derived from runtime telemetry and ledger analytics:

| Signal | Description | Implication |
|--------|-------------|-------------|
| Semantic duplication | Identical semantics via different projections | Missing kernel abstraction |
| Replay complexity | Excessive userland reconstruction on replay | Missing transition semantics |
| Invariant violation frequency | Contracts fail under valid inputs | Semantics misaligned with reality |
| Fitness divergence | CIT/MIT/EIT/AIT drift beyond tolerance | Meaning model insufficient |
| Contract redundancy | Userland contracts mimic kernel contracts | Kernel boundary eroding |

Implementation: `src/continuity/crk2_boundary_control.py`

---

## T2.6 Outer-loop control system

CRK-T2 is modeled as a **discrete outer loop** over kernel version `k(t)`.

### State

\[
x_{\text{outer}}(t) = \bigl[k(t),\ \bar{I}(t)\bigr]
\]

- `k(t) ∈ ℕ` — active kernel version (CRK-1 → CRK-2 → …)
- `\bar{I}(t)` — smoothed insufficiency signal

### Telemetry (inputs from inner loop)

\[
s(t) = \bigl[s_{\text{dup}},\ s_{\text{replay}},\ s_{\text{viol}},\ s_{\text{fit}},\ s_{\text{red}}\bigr]^\top \in [0,1]^5
\]

### Insufficiency functional

\[
I(t) = w^\top s(t), \quad w_i \geq 0,\ \sum_i w_i = 1
\]

### Temporal smoothing (EMA)

\[
\bar{I}(t) = \alpha I(t) + (1-\alpha)\bar{I}(t-1), \quad 0 < \alpha \leq 1
\]

### Amendment control law (hysteresis)

Discrete action `u(t) ∈ {0,1}`:

- `u(t) = 0` — no amendment
- `u(t) = 1` — initiate kernel amendment process

Thresholds `\theta_{\text{low}} < \theta_{\text{high}}`. Require `\bar{I} \geq \theta_{\text{high}}` for `N` consecutive epochs before `u=1`. Clear when `\bar{I} \leq \theta_{\text{low}}`.

### Kernel version update

Governance ratification `r(t) ∈ {0,1}`:

\[
k(t+1) = k(t) + u(t)\cdot r(t)
\]

### CRK-T1 constraint on admissible kernels

For any `k`, the kernel configuration must satisfy CRK-1 form: five objects, four contracts, replayable transitions.

- **CRK-T1** defines the admissible state space for `k`.
- **CRK-T2** defines the control law that moves `k` within that space.

---

## T2.7 Amendment conditions

A kernel amendment (CRK-2+) is justified when:

1. Insufficiency signals persist across ≥ 3 epochs (`N` consecutive above `\theta_{\text{high}}`).
2. Userland expression causes contract violation or semantic duplication.
3. Replay complexity exceeds configured threshold.
4. Governance stewards confirm the missing abstraction cannot be derived from existing objects or contracts.

---

## T2.8 Boundary symmetry

| Theorem | Function | Protects against |
|---------|----------|------------------|
| CRK-T1 — Constitutional Sufficiency | Defines minimal kernel ontology | Ontological inflation |
| CRK-T2 — Constitutional Boundary Detection | Detects insufficiency; triggers amendment | Permanent stagnation |

Together they form the **Adaptive Constitutional Kernel** — minimal and self-aware.

---

## Appendix — CRK-T1 ↔ CRK-T2 dual boundary

```text
                         ┌──────────────────────────────────────┐
                         │      CONSTITUTIONAL KERNEL (CRK-1)    │
                         ├──────────────────────────────────────┤
                         │  Five Objects · Four Contracts        │
                         │  Canonical Transitions · Replay       │
                         └──────────────────────────────────────┘
                                      ▲             ▲
                                      │ CRK-T1      │ CRK-T2
                                      │ Sufficiency │ Boundary Detection
                                      ▼             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                 CONSTITUTIONAL APPLICATION SPACE (USERLAND)              │
├──────────────────────────────────────────────────────────────────────────┤
│  Fitness: SIT, GIT, PIT, EIT, CIT, MIT, AIT                            │
│  Panels, dashboards, agents, policies, discovery pods                    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## T2.9 Document history

- **v0.1** — Initial proposal (2026). Complements CRK-T1; outer-loop control in `crk2_boundary_control.py`.
