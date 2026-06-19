# PROOF-1 Institutional MRI Integration

## Status
Implemented in `@aaes-os/mri-instrument` and exposed to operators through `GET /mri/v2`.

## Runtime Contract
MRI v0.2 emits:

- `state_vector`: continuity, governance, memory, coordination, confidence.
- `delta_state`: normalized state change from the previous measurement.
- `trajectory_vector`: confidence-weighted motion over state dimensions.
- `benchmarks`: current, previous, industry average, and top quartile marker data.
- `trajectory_signatures`: operator-readable movement classifications.
- `trajectory_breakdown`: per-dimension delta, confidence, contribution, and direction.
- `projection`: short-horizon public state projection.
- `risks`, `interventions`, `evidence`, and `before_after`.

## Evidence
- Code: `packages/mri-instrument/src/mriV2.ts`
- Tests: `packages/mri-instrument/src/mriV2.test.ts`
- Operator endpoint: `services/ops-console/src/server.ts`
- Endpoint test: `services/ops-console/src/server.test.ts`

## Promotion Path
The `invariant_fitness` result supports the soft invariant lifecycle:

1. propose invariant;
2. apply intervention;
3. measure state delta;
4. evaluate promote, retain, or revert;
5. write receipt through the evidence and enforcement layers.
