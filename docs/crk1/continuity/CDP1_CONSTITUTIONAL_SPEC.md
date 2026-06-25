# CDP-1 — Continuity Demonstration Protocol (Constitutional Spec)

## Preamble

Where CRR-1 preserves calibration, and CLG-1 preserves lineage, continuity is not proven until a steward who did not experience the original contradiction becomes more calibrated after replaying preserved lineage.

**CDP-1** defines the constitutional experiment required to demonstrate continuity propagation.

## Article I — Definitions

### Assimilation

A measurable improvement in judgment after lineage replay.

### Assimilation Delta (ΔA)

```
ΔA = Q_post − Q_pre
```

### Assimilation Threshold (τA)

Minimum ΔA required to claim continuity propagation.

### Independent Steward (S₂)

A steward who did not participate in the original contradiction.

## Article II — Constitutional Requirements

A valid CDP-1 run must satisfy:

| Requirement | Description |
|-------------|-------------|
| **Isolation** | S₂ must prove non-participation in the original contradiction |
| **Pre-Measurement** | S₂ performs a judgment task exposing the same contradiction class |
| **Lineage Replay** | S₂ reconstructs CRR-1 and CLG-1 without external guidance |
| **Post-Measurement** | S₂ performs the same judgment task again |
| **Assimilation Test** | ΔA ≥ τA |
| **Proof Emission** | S₂ emits a CAA-1 receipt |
| **Governance Validation** | Proof Layer validates lineage, isolation, ΔA, and proof bundle |

## Article III — Protocol Output

CDP-1 produces:

- Pre-measurement trace
- Post-measurement trace
- ΔA computation
- CAA-1 receipt
- Governance validation report

## Article IV — Constitutional Status

CDP-1 is the **final continuity object**.

It is not a record.  
It is a **repeatable experiment**.

Continuity is not asserted — it is **demonstrated**.

## Implementation

| Component | Path |
|-----------|------|
| Experiment harness | `sdk/continuity-sdk/harness/cdp1_experiment.py` |
| Mission #006 runner | `src/crk1/mission_006_calibration_assimilation.py` |
| CAA-1 builder | `src/crk1/caa1_assimilation.py` |

## Related

- [CDP1_GOVERNANCE_RULES.md](../governance/CDP1_GOVERNANCE_RULES.md)
- [CDP1_REPRODUCIBILITY_STANDARD.md](../standards/CDP1_REPRODUCIBILITY_STANDARD.md)
- [CDP1_PUBLIC_OVERVIEW.md](../../public/CDP1_PUBLIC_OVERVIEW.md)
- [CEP_OVERVIEW.md](../../../sdk/continuity-sdk/CEP_OVERVIEW.md)
