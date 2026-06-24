# continuity-engine API Reference (v1.0)

## Core domains

| Domain | Purpose |
|--------|---------|
| CSS-2 | Threshold + observer stewardship |
| CRK-1 | Constitutional invariants + observer protection |
| JPSS-2 | Observer development pipeline |
| RA-COS-1 | Evidence loop + trace |
| Transformation Law | Reality → Truth → Memory → Continuity → Evolution |
| Stewardship | Observer drift, capture, effectiveness |
| Registry | Threshold storage (DB + memory) |
| Governance | Δ-threshold legitimacy + adversarial review |
| Lineage | Threshold history, drift, charts |
| Audit | Reality-earns-architecture test |

## CSS-2

### Types

`Threshold`, `ThresholdDelta`, `ThresholdVersion`, `ObservationPattern`, `ProtoThreshold`, `ObserverProfile`, `ThresholdLifecycle`

### Functions

- `createThreshold()` — `css2/threshold.ts`
- `applyThreshold()` — classify observed value against threshold
- `applyThresholdDelta()` — merge delta into threshold document
- `createObservationPattern()` — `css2/patterns.ts`
- `createProtoThreshold()` — `css2/proto-threshold.ts`
- `runThresholdLifecycle()` — `css2/threshold-lifecycle.ts`
- `runObserverLifecycle()` — `css2/observer-lifecycle.ts`

## CRK-1

- `enforceCRKOnThresholdDelta(delta, invariantSet)` — `crk1/recalibration-guard.ts`
- `enforceObserverProtection(context)` — `crk1/observer-protection.ts`
- `defaultInvariantSet` — `crk1/invariants.ts`

## JPSS-2

- `JPSS2_CURRICULUM` — `jpss2/curriculum.ts`
- `applyCurriculumModule(observer, module)` — `jpss2/apply-curriculum.ts`
- `advanceObserverStage(observer)` — `jpss2/observer-development.ts`
- `evaluateObserverCapabilities(observer)` — `css2/observer-lifecycle.ts`

## RA-COS-1

- `runEvidenceLoop(handlers)` — continuous evidence stream
- `processRACosEvent(deps, event, drift, validation)` — recalibration event loop slice
- `detectRecalibrationTriggers(...)` — trigger heuristics
- `InMemoryObserverTraceStore` — observer trace subsystem
- `makeObservationTrace()`, `makePatternTrace()`, `makeProtoThresholdTrace()`, `makeThresholdDeltaTrace()`, `makeObserverDriftTrace()`

## Transformation Law

- `realityToTruth()` — `transformation/truth.ts`
- `truthToMemory()` — `transformation/memory.ts`
- `memoryToContinuity()` — `transformation/continuity.ts`
- `continuityToEvolution()` — `transformation/evolution.ts`

## Stewardship

- `evaluateObserverStewardship()`
- `evaluateObserverEffectiveness()`
- `computeObserverDrift()`
- `detectObserverCapture()`

## Registry

- `ThresholdRegistry` (interface)
- `InMemoryThresholdRegistry`
- `DbThresholdRegistry` (abstract)

## Governance

- `RecalibrationGovernanceEngine`
- `runAdversarialReview()`
- `scoreLegitimacy()`

## Lineage

- `generateLineageReport()`
- `generateThresholdChartSpec()`
- `generateDriftHeatmap()`

## Audit

- `auditProject()` — reality-earns-architecture test

## CLI

```bash
npx thresholdctl lineage <thresholdId>
npx thresholdctl chart <thresholdId>
npx thresholdctl invariants
```
