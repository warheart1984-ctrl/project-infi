# Theta Canon Invariants

## Invariant NC-Phi.1 - Capacity for Lawful Continuation

For any cosmos state `S_t`, the lawful capacity for continuation `Phi(S_t)` is defined as the difference between constitutional constraint and accumulated mass-like commitments.

```text
Phi(S_t) = C(S_t) - M(S_t)
```

Where:

| Functional | Meaning |
|------------|---------|
| `C(S_t)` | Constraint functional: maps the current cosmos to its constitutional boundary, or how much lawful movement is permitted |
| `M(S_t)` | Mass functional: maps the current cosmos to its inertial load, including accumulated commitments, tensions, and obligations that resist change |
| `Phi(S_t)` | Continuation capacity: remaining lawful room for evolution, motion, or negotiation |

### Constraint

```text
Phi(S_t) >= 0
```

If `Phi(S_t) < 0`, the system is in constitutional violation: it is attempting more change than law and commitments allow.

### Concrete Cosmos Functionals

Assuming a cosmos model with zones, zone tension vectors, propagation links, paradox state, governance constraints, and active obligations:

```text
M(S_t) =
  sum over z in Z of norm(T_z)
  + sum over o in Obligations(S_t) of w_o
```

Where:

| Term | Meaning |
|------|---------|
| `Z` | Set of zones |
| `T_z` | Tension vector in zone `z` |
| `norm(T_z)` | L1, L2, or specified norm of zone tension |
| `Obligations(S_t)` | Active commitments such as governance promises or scheduled actions |
| `w_o` | Weight or importance of obligation `o` |

Mass is how much is already loaded into the system: tension plus promises.

```text
C(S_t) =
  sum over z in Z of max_tension_z
  - sum over c in ActiveConstraints(S_t) of lambda_c
```

Where:

| Term | Meaning |
|------|---------|
| `max_tension_z` | Constitutional upper bound for zone `z` |
| `ActiveConstraints(S_t)` | Currently binding constraints, such as no topology change or no paradox escalation |
| `lambda_c` | Strength or penalty of constraint `c` |

Constraint is how much lawful room exists before the cosmos hits its constitutional walls.

### Runtime Rule

The Negotiant Core may only apply transitions whose total change does not exceed the current capacity for lawful continuation.

```text
Phi(S_t) >= Delta(S_t -> S_t+1)
```

Where `Delta(S_t -> S_t+1)` is the magnitude of attempted state change between ticks, such as tension delta, topology delta, or aggregate mutation measure.

If:

```text
Delta(S_t -> S_t+1) > Phi(S_t)
```

then the transition must be rejected and recorded as a constitutional error.

### coreTick Enforcement

```text
coreTick Pipeline (v1.1)

1. cloneCosmos()
2. assertTransitionInvariants()
3. computeContinuationCapacity()      # NC-Phi.1
4. computeProposedDelta()
5. assert(Delta <= Phi)
6. applyLocalTensionRules()
7. applyPropagationRules()
8. resolveParadoxEvents()
9. finalizeCosmos()
```

The pre-transition gate is:

```text
Phi_t = C(S_t) - M(S_t)
Delta_t = norm(S_t -> S_t+1*)

if Delta_t > Phi_t:
    raise ConstitutionalError("Transition exceeds lawful continuation capacity")
```

`S_t+1*` is the candidate next state before finalization.

### Ledger Fields

`zoneTick` and `coreTick` receipts must include:

```text
continuation_capacity_t: Phi_t
proposed_delta_t: Delta_t
capacity_check_passed: boolean
```

Canonical receipt shape:

```text
zoneTick
  timestamp
  cosmos_hash_before
  cosmos_hash_after
  version_info
  continuation_capacity_t
  proposed_delta_t
  capacity_check_passed
  payload
```

### Cockpit Indicators

NC-Phi.1 introduces three first-class cockpit indicators:

| Indicator | Meaning |
|-----------|---------|
| `indicator.continuation_capacity` | Current `Phi_t` |
| `indicator.capacity_utilization` | `Delta_t / Phi_t`, with explicit handling for zero capacity |
| `indicator.capacity_risk_band` | Operational risk band derived from utilization and verification status |

Each indicator must define a normative definition, reference implementation, independent verifier, provenance metadata, and verification status.
