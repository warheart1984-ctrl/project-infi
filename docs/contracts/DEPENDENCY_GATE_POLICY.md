# Dependency Gate Policy

This contract governs how dependencies enter and remain inside AAIS.

Dependencies are not neutral plumbing.
They are ingress surfaces.

If a dependency is unknown, drifting, unverifiable, or carrying an unreviewed
security delta, it is not admitted into governed runtime truth.

## Core Doctrine

Stability before freedom applies to dependencies too.

- Stability without dependency control creates silent drift.
- Freedom without dependency control creates unbounded ingress.
- Therefore dependency change must be governed before it is convenient.

## Active Rules

1. Security-sensitive dependencies must be pinned to known-good versions.
2. Lockfiles are admission evidence, not optional convenience files.
3. Where the package manager supports hashes or integrity fields, those fields
   are part of the governed state.
4. Unknown, drifting, or partially regenerated dependency state fails closed.
5. A dependency change is incomplete until verification passes on the affected
   runtime surfaces.

## Repo Expectations

The current repo uses these governed evidence surfaces:

- `api/uv.lock`
- `frontend/package-lock.json`
- `mobile/package-lock.json`

The current repo also uses explicit npm overrides where a safe transitive
version must be forced instead of waiting for an upstream package to catch up.

## Verification Requirement

Dependency changes must be followed by the relevant verification slices:

- backend tests for Python/runtime-impacting changes
- frontend tests and production build for frontend lock changes
- mobile typecheck or other mobile CI slices for mobile lock changes
- dependency audit checks where the hardening pass is security-driven

## Traceability Requirement

A dependency hardening pass must update:

- `docs/audit/AAIS_STATUS_AUDIT.md`
- `docs/audit/LOGBOOK.md`

This keeps dependency state visible as governed project history instead of
silent package drift.
