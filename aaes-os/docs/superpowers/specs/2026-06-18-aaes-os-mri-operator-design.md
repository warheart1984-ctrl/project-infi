# AAES OS MRI Operator Pilot Design

## Goal

Build the Continuity Index / MRI v0.1 as an AAES OS-only operator pilot slice. The slice must not touch the project-level `frontend` app. It lives in `aaes-os`, exposes testable TypeScript instrument logic, and gives the AAES OS ops console a seeded operator readout.

## Scope

The first slice implements:

- Continuity, governance, memory, and confidence scoring.
- Institutional state vector `S(t) = [R, K, G, D, X]`.
- Delta state `S(after) - S(before)`.
- Risk detection for single points of failure, documentation gaps, governance ambiguity, decision bottlenecks, and coordination overload.
- Confidence-weighted intervention ranking.
- Before/after report generation.
- Seeded AAES OS operator endpoint and console section.

The slice deliberately excludes backend persistence, external organization intake, authentication changes, and project-level frontend routes.

## Architecture

Create a new workspace package at `aaes-os/packages/mri-instrument`. It owns all formulas and report generation as pure TypeScript functions. The ops console imports the package through a workspace dependency and exposes `GET /mri`, which returns a deterministic seeded before/after assessment for operators.

The ops console UI remains compact and internal. It fetches `/mri` alongside `/telemetry`, then renders score readouts, state delta, risks, interventions, and the generated before/after report summary in the existing AAES OS console.

## Data Flow

1. Seed before/after `OrgMeasurement` inputs in `services/ops-console/src/mriState.ts`.
2. Run `runMRIComparison(before, after)`.
3. Compute scores, confidence, state vectors, delta state, risks, interventions, and report.
4. Serve the result from `GET /mri`.
5. Render the result in `App.tsx`.

## Error Handling

Instrument functions clamp score outputs to `0..100` and confidence to `0..1`. Ratio calculations handle zero denominators by returning `0` instead of `NaN` or `Infinity`. The seeded endpoint is deterministic, so endpoint errors should only come from unexpected runtime failure.

## Testing

Use TDD in the new package:

- Scoring formulas and denominator guards.
- Confidence formula.
- Delta state.
- Risk detection.
- Confidence-weighted intervention ranking.
- Before/after report generation.

Add an ops-console server test for `GET /mri`.

## Files

- `aaes-os/packages/mri-instrument/*`: new package.
- `aaes-os/tsconfig.base.json`: workspace path alias.
- `aaes-os/vitest.config.ts`: root test alias.
- `aaes-os/services/ops-console/package.json`: workspace dependency.
- `aaes-os/services/ops-console/tsconfig.json`: package reference.
- `aaes-os/services/ops-console/vite.config.ts`: proxy `/mri`.
- `aaes-os/services/ops-console/vitest.config.ts`: alias for tests.
- `aaes-os/services/ops-console/src/mriState.ts`: seeded assessment.
- `aaes-os/services/ops-console/src/server.ts`: `GET /mri`.
- `aaes-os/services/ops-console/src/server.test.ts`: endpoint coverage.
- `aaes-os/services/ops-console/src/App.tsx`: operator readout.

## Self Review

- No project-level frontend files are in scope.
- The instrument package is independently testable.
- The operator readout is seeded and deterministic.
- No persistence is promised in this slice.
- No placeholders or deferred requirements remain for the pilot scope.
