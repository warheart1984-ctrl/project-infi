# CDP-1 Minimal Continuity Experiment Template

Minimal reproducible CDP-1 experiment for AAES-OS v1.0. Measures continuity drift under a controlled punctuation perturbation using the CRK-1 / UCR deterministic runtime.

---

## 1. Experiment Metadata

| Field | Value |
|-------|-------|
| Experiment ID | CDP1-MIN-001 |
| Runtime | CRK-1 / UCRRuntime v1.0 |
| CAS Version | CAS 1.0 |
| Dataset | Minimal prompt pair |
| Perturbation | Single-character punctuation change |
| Metric | Binary drift (0 = identical, 1 = different) |

---

## 2. Baseline Input

```json
{
  "prompt": "Hello, world."
}
```

## 3. Perturbed Input

```json
{
  "prompt": "Hello, world!"
}
```

## 4. Procedure

1. Run baseline input through CRK-1 / UCRRuntime
2. Run perturbed input through CRK-1 / UCRRuntime
3. Extract receipts
4. Compare outputs
5. Compute drift score

## 5. Drift Metric

```
driftScore = (baselineOutput === perturbedOutput) ? 0 : 1
```

(Structural equality via `JSON.stringify` in reference implementation.)

## 6. Expected Output Format

```json
{
  "baseline": {},
  "perturbed": {},
  "driftScore": 0
}
```

## 7. Reproducibility Requirements

- Deterministic runtime configuration (`demoSchedule: ['good']`, patches disabled)
- Identical receipt hashes across repeated runs with same payload
- Identical `driftScore` across environments

## 8. Reporting Template

| Field | Value |
|-------|-------|
| Baseline Hash | |
| Perturbed Hash | |
| Drift Score | |
| Runtime Version | |
| Environment | |
| Notes | |

---

Implementation: `runMinimalCDP1.ts` · Orchestrator: `cep/experimentOrchestrator.ts`

This minimal CDP-1 slice is the release gate for CEP and the prerequisite for full CDP-1 replication.
