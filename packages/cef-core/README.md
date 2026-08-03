# `@aaes-os/cef-core`

CEF v1.0 **core** package — unified evidence schemas, Ajv validation, profile registry, and structural invariant checks.

Charter: [`docs/release/cef/CEF_V1_CHARTER.md`](../../docs/release/cef/CEF_V1_CHARTER.md)  
(includes Article III Reality axiom and Article III-A Epistemic Cycle — **declared** in charter; this package **enforces** schema + structural invariants only.)

## Purpose

Single canonical source of truth for CEF evidence schemas and validation used by OEL, CREC, CEL, Security, and ModelEval profiles.

## Validate core evidence

```ts
import { validateEvidence } from '@aaes-os/cef-core';

const { valid, errors } = validateEvidence(evidenceObject);
```

## Validate a profile

```ts
import { validateProfile } from '@aaes-os/cef-core';

const { valid, errors } = validateProfile('OEL', evidenceObject);
```

Profiles: `CREC` | `OEL` | `CEL` | `Security` | `ModelEval`

## Structural invariants

```ts
import { checkInvariants, allInvariantsPassed } from '@aaes-os/cef-core';

const checks = checkInvariants(evidenceObject);
```

Covers charter invariants 1–6 at the structural layer (required fields, replay, audit, authority, semver, promotion decision).

## Claim≠evidence promotion gate

```ts
import { assertPromotionAllowed, claimExceedsEvidence } from '@aaes-os/cef-core';

const gate = assertPromotionAllowed(evidenceObject);
// fails when promotion.decision === "approved" while any check is still "pending"
```

Consumers: `@aaes-os/cef-certification`, `@aaes-os/cef-stewardship`, `pnpm oel:validate`.

## Add a new profile

1. Add `src/schemas/cef-<name>-evidence.json` with `allOf` + `$ref` to the core `$id`
2. Register in `src/registry/profiles.ts` (`CEF_PROFILES` + `CefProfileType`)
3. Extend `CefEvidence` in `src/types/Evidence.ts` if needed
4. Add tests under `tests/profile-schema.test.ts`

## Certification Engine integration (declared)

Downstream Certification / Stewardship engines **should** call `validateProfile` before promotion decisions. This package does **not** implement the Certification Engine itself.

## Scripts

```bash
pnpm --filter @aaes-os/cef-core test
pnpm --filter @aaes-os/cef-core build
```
