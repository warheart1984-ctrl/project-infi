# CRK-1 Operational Piping Runbook (Local Governed Inference)

## Objective

Establish a fully governed, end-to-end local inference path using CRK-1:

- All governed calls flow through a single adapter.
- Invariants (K0–K12) are enforced pre/post.
- CE-1 / CRR-1 / CLG-1 are invoked as designed.
- Receipts + lineage are emitted for every run.
- No side-door / raw model calls from the operator path.

---

## Target Artifacts

| Role | Path |
|------|------|
| Core adapter | `src/runtime/governedPredict.ts` |
| Local model client | `src/model/localClient.ts` |
| Invariants | `src/governance/invariants.ts` |
| Receipts | `src/governance/receipts.ts` |
| Lineage | `src/governance/lineage.ts` |
| CLI entrypoint | `bin/run_local_governed.ts` |
| Config | `config/local-governed.yaml` |
| Smoke test | `tests/local_governed_smoke.test.ts` |

---

## A. Operator Kernel Health

### A1. Operator identity

**Requirement:** every governed call carries a stable operator id.

- Field: `operator_id: string`
- Source: config (`config/local-governed.yaml`) or env (`OPERATOR_ID`).
- Must appear in: `GovernedContext`, receipts, lineage root.

### A2. Receipts

**Requirement:** every governed call emits a receipt.

Minimum fields:

- `call_id`
- `operator_id`
- `timestamp`
- `invariant_set_version`
- `mode` (predict / observe / correct)
- `invariants_passed: boolean`

Implementation: `src/governance/receipts.ts`

---

## B. AAIS Local Inference Path

### B1. Local-only model client

File: `src/model/localClient.ts`

```ts
export async function localPredict(input: string, opts: LocalModelOptions): Promise<string>;
```

Uses local weights only (no remote calls). `localPredict` must only be called from `governedPredict`.

### B2. Governed adapter

File: `src/runtime/governedPredict.ts`

```ts
export async function governedPredict(
  input: string,
  context: GovernedContext
): Promise<GovernedResult>;
```

Responsibilities:

1. Load invariants (K0–K12) and `invariant_set_version`.
2. Run pre-call admissibility checks.
3. Call `localPredict(...)`.
4. Run CE-1 / CRR-1 / CLG-1 post-call hooks.
5. Emit receipt + lineage entry.

---

## C. End-to-End Governed Pipeline

### C1. CLI — `bin/run_local_governed.ts`

1. Load `config/local-governed.yaml`.
2. Construct `GovernedContext`.
3. Call `governedPredict(prompt, context)`.
4. Print model output, receipt summary, lineage root id.

### C2. Config — `config/local-governed.yaml`

```yaml
model_path: "./models/local-llm"
operator_id: "local-operator-001"
invariant_set_version: "K0-K12-v1"
log_receipts: true
log_lineage: true
```

---

## D. Tests

### D1. Smoke test — `tests/local_governed_smoke.test.ts`

Happy path: `governedPredict` returns output, receipt with `invariants_passed: true`, lineage `root_id`.

Refusal path (optional v0.2): prompt that triggers invariant failure.

---

## E. Success Criteria

- [ ] `bin/run_local_governed.ts` runs using local weights only
- [ ] All calls go through `governedPredict`
- [ ] Receipts + lineage are emitted
- [ ] `tests/local_governed_smoke.test.ts` passes
- [ ] No direct/raw model calls from operator-facing code
