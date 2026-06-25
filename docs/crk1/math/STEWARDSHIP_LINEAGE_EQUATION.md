# Stewardship Lineage Equation

Formal derivation — mathematical backbone of CLG-1 and CAA-1.

## 1. Definitions

Let:

- **S_t** = steward at time t
- **C_t** = calibration event at time t
- **L_t** = lineage state at time t
- **ΔA_t** = assimilation delta at time t

## 2. Calibration Preservation

A calibration event is preserved if:

```
C_t ∈ L_{t+1}
```

## 3. Lineage Connectivity

Lineage is connected if:

```
C_t → C_{t+1} ⟺ ∃ shared contradiction class
```

## 4. Steward Reconstruction

A steward S_{t+k} reconstructs calibration if:

```
Ĉ_t = Replay(L_{t+k})
```

Where Ĉ_t is the steward's internal reconstruction.

## 5. Assimilation Condition

Assimilation occurs if:

```
ΔA_{t+k} = Q_post − Q_pre ≥ τ_A
```

## 6. Stewardship Lineage Equation

Continuity propagates across stewards if:

```
S_{t+k} ← Assimilation(C_t)
```

Formally:

```
ΔA_{t+k} ≥ τ_A  ∧  Ĉ_t = C_t  ∧  C_t ∈ L_{t+k}
```

This is the **Stewardship Lineage Equation**.

A calibration event at time t propagates to a steward at time t+k if and only if the steward reconstructs the calibration, assimilates it, and achieves measurable improvement above threshold.

## Related

- [CPM.md](../metrics/CPM.md)
- [STEWARDSHIP_LINEAGE_EQUATION.md](../math/STEWARDSHIP_LINEAGE_EQUATION.md) — this document
- [CLG1_CALIBRATION_LINEAGE_GRAPH.md](../continuity-os/CLG1_CALIBRATION_LINEAGE_GRAPH.md)
