# continuity-engine API Reference (v1.0)

## Core domains

| Domain | Purpose |
|--------|---------|
| **RPA-1** | Root invariant — reality primacy + Reality Veto |
| **JPA-1** | Constitutional judgment primacy (contains OPA-1) |
| **Judgment** | First-class judgment capability runtime + cycles |
| CSS-2 | Threshold + observer stewardship (judgment-preserving) |
| CRK-1 | Constitutional invariants + observer protection + consequence kernel |
| JPSS-2 | Observer development pipeline |
| RA-COS-1 | Evidence loop + trace |
| Transformation Law | Reality → Truth → Memory → Continuity → Evolution |
| Stewardship | Observer drift, capture, effectiveness |
| Registry | Threshold storage (DB + memory) |
| Governance | Δ-threshold legitimacy + adversarial review + Reality Veto gate |
| **Ledger** | Continuity Ledger v2 — cycles, veto receipts, health views |
| Lineage | Threshold history, drift, charts |
| Audit | Reality-earns-architecture test |

## JPA-1 (Judgment Primacy)

Constitutional invariant: continuity = preserved capacity for sound, reality-responsive judgment.

- `JPA1_PRINCIPLES`, `JPA1_8_JUDGMENT_FAILURE`, `OPA1_CONTAINMENT` — `jpa1/spec.ts`
- `JUDGMENT_PRESERVING_SYSTEMS` — `jpa1/system-mandates.ts`
- `assessObserverJudgment()`, `assessJudgmentCapability()` — `jpa1/judgment-capability.ts`
- `assessJPA1Compliance()` — `jpa1/compliance.ts`

Whitepaper section: `docs/CSS-2-WHITEPAPER-JPA-1.md`

## RPA-1 (Reality Primacy)

Root constitutional invariant: reality is the final arbiter of judgment.

- `RPA1_PRINCIPLES`, `RPA1_CONTINUITY_DEFINITION` — `rpa1/spec.ts`
- `issueRealityVeto()`, `detectRealityDivergence()` — `rpa1/reality-veto.ts` (RV-1, RV-2)
- `buildMandatoryReconsiderationCycle()` — RV-3 mandatory reconsideration
- `escalateIgnoredVeto()` — RV-4 governance escalation
- `InMemoryRealityVetoLedger` — legacy veto store (prefer `InMemoryContinuityLedger`)

## Continuity Ledger v2

Cycle-centric ledger with Reality Veto receipts and lineage health.

- `ContinuityLedger`, `InMemoryContinuityLedger` — `ledger/continuity-ledger.ts`
- `ThresholdView`, `RecalibrationView`, `ContinuityHealthReport` — `ledger/types.ts`
- `getContinuityHealth()`, `getFailedLineages()`, `getThresholdViews()` — lineage queries

## Governance Reality Veto

Structural veto detection and corrigibility gate for Δ-threshold decisions.

- `detectRealityVeto()`, `processRealityVeto()` — `governance/reality-veto.ts`
- `applyGovernanceWithRealityVeto()` — blocks non-corrigible judgment cycles (CRK-1.J / RPA-1)

Docs: `docs/CONSTITUTIONAL-FAILURE-MODES.md`, `docs/REALITY-EVIDENCE-JUDGMENT-STACK.md`


## Judgment module

Six-dimension capability vector: perception, interpretation, valuation, deliberation, commitment, reflection.

- `JudgmentCapability`, `emptyJudgmentCapability()` — `judgment/capability.ts`
- `evaluateJudgment()`, `isJudgmentFailure()` — `judgment/evaluation.ts`
- `computeJudgmentDrift()` — `judgment/drift.ts`
- `correctJudgmentToward()` — `judgment/correction.ts`
- `judgmentFromObserver()` — `judgment/mapping.ts` (ObserverProfile → JudgmentCapability)
- `JudgmentCycle`, `assessCorrigibility()`, `annotateCorrigibility()` — `judgment/cycle.ts` (CRK-1.J.5)
- `JudgmentCycleLedger`, `recordJudgmentCycle()` — `judgment/cycle-ledger.ts`

See: `docs/SOUND-JUDGMENT-CYCLE.md`

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
- `assessLegitimateJudgment()` — `crk1/legitimate-judgment.ts` (CRK-1.J + J.5 corrigibility)
- `buildLegitimateJudgmentInput()` — governance bridge
- **Consequence kernel (K0–K3):** `proposeDecision()`, `allocateResource()`, `executeDecision()`, `replayOutcome()` — `crk1/consequence-kernel.ts`
- `InMemoryConsequenceLedger`, `runConsequencePipeline()` — `crk1/consequence-ledger.ts`, `crk1/consequence-pipeline.ts`
- `validateK01()`, `validateK21()`, `validateConsequenceChain()` — `crk1/consequence-invariants.ts`
- `proveAntiInsulation()`, `detectInsulatedDecisions()` — `crk1/anti-insulation.ts`

Whitepapers: `docs/CRK-1-WHITEPAPER-LEGITIMATE-JUDGMENT.md`, `docs/CRK-1-WHITEPAPER-CONSEQUENCE-KERNEL.md`

## JPSS-2

- `JPSS2_CURRICULUM` — `jpss2/curriculum.ts` (legacy observer modules)
- `JPSS2_JUDGMENT_CURRICULUM` — `jpss2/judgment-curriculum.ts` (JPSS-2.J six dimensions)
- `applyCurriculumModule()` / `applyJudgmentCurriculumModule()`
- `JudgmentCapabilityLedger`, `createCapabilityLedger()`, `updateCapabilityLedger()` — `jpss2/capability-ledger.ts`
- `advanceObserverStage(observer)` — `jpss2/observer-development.ts`

Whitepaper: `docs/JPSS-2-WHITEPAPER-JUDGMENT-CURRICULUM.md`

## RA-COS-1

- `runEvidenceLoop(handlers)` — continuous evidence stream
- `processRACosEvent(deps, event, drift, validation)` — recalibration event loop slice
- `detectRecalibrationTriggers(...)` — trigger heuristics
- `InMemoryObserverTraceStore` — observer trace subsystem
- `JudgmentDriftEvent`, `recordJudgmentDriftEvent()`, `makeJudgmentDriftTrace()` — `ra-cos1/judgment-drift-trace.ts`
- `makeObservationTrace()`, `makePatternTrace()`, `makeProtoThresholdTrace()`, `makeThresholdDeltaTrace()`, `makeObserverDriftTrace()`

Whitepaper: `docs/RA-COS-1-WHITEPAPER-JUDGMENT-DRIFT.md`

## Constitutional Stack

Hierarchy diagram (JPA-1 → OPA-1 → CSS-2 → CRK-1 → RA-COS-1): `docs/CONSTITUTIONAL-STACK.md`

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

- `RecalibrationGovernanceEngine` — evaluates Δ-thresholds with CRK-1 + CRK-1.J + adversarial review
- `GovernanceContext.judgmentAssessment` — optional JPA-1 assessment for full CRK-1.J gate
- `applyDeltaWithCRKGuard()` — registry apply with CRK-1 + CRK-1.J pre-check
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
