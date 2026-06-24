# Reality → Evidence → Judgment → Stewardship → Continuity

Causal stack diagram for constitutional continuity.

## Text Diagram (slides)

```
[Reality]
   |
   v
[Evidence]
   |  (RA-COS-1: preserve signals)
   v
[Judgment]
   |  (OPA-1: see reality)
   |  (JPA-1: run reality-correctable cycles)
   v
[Stewardship]
   |  (transmit judgment-under-reality across generations)
   v
[Continuity]
```

## Side Constraint (RPA-1)

Reality retains ultimate authority over every layer via evidence.

## Failure Mode

If any layer severs evidence from reality, continuity begins to fail even if the machinery keeps running.

## Annotations

| Margin | Label |
|--------|-------|
| Left | Reality is the source |
| Middle | Evidence is the test |
| Right | Architecture is the consequence |

## Constitutional Stack Ordering (top-down)

```
RPA-1        Reality Primacy
OPA-1        Observer Primacy
RA-COS-1     Evidence Preservation
JPA-1        Judgment Primacy (reality-correctable cycles)
CRK-1.J      Legitimate Judgment
CSS-2        Threshold & Δ-Threshold Governance
Stewardship  Lineage of authority under reality
Continuity   Emergent property of the whole stack
```

## Runtime Artifacts

| Artifact | Module |
|----------|--------|
| `JudgmentCycle` | `src/judgment/cycle.ts` |
| `RealityVetoReceipt` | `src/rpa1/reality-veto.ts` |
| `ContinuityLedger` | `src/ledger/continuity-ledger.ts` |
| `detectRealityVeto` / `processRealityVeto` | `src/governance/reality-veto.ts` |
| `applyGovernanceWithRealityVeto` | `src/governance/reality-veto.ts` |

## Tagline

> Reality is the source. Evidence is the test. Architecture is the consequence.
