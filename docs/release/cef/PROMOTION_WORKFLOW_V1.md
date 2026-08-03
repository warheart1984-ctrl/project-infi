# Promotion Workflow v1.0

**Status:** Specified — CEF v1.0  
**Engine:** [CERTIFICATION_ENGINE_V1.md](./CERTIFICATION_ENGINE_V1.md)

A governed workflow for promoting evidence into certificates.

## Stage 1 — Evidence Collection

1. Gather all required evidence for the profile.
2. Bind evidence to CAR (authority).
3. Produce initial Evidence Record conforming to CEF core (+ profile extension).

## Stage 2 — Verification Gates

All gates must pass:

- Integrity
- Completeness
- Security (SBOM, supply chain, vulnerability)
- Conformance tests
- Policy validation (for OEL: NetPol, RBAC, securityContext)
- Replay determinism
- Audit visibility

## Stage 3 — Authority Check

1. Validate CAR.
2. Ensure actor has promotion authority.
3. Confirm scope and constraints.

## Stage 4 — Promotion Decision

1. Decision: `approved` or `rejected` (or remain `hold`).
2. Decision MUST be logged as a CDR (constitutional decision record).
3. Decision MUST reference evidence.

## Stage 5 — Signature

1. Promotion signature binds certificate to authority.
2. Signature is immutable.

## Stage 6 — Certificate Creation

1. Certificate is generated from evidence.
2. Certificate becomes immutable upon promotion.

## Stage 7 — Publication

1. Certificate is published to the evidence ledger / release surface.
2. Certificate becomes auditable.

## Stage 8 — Stewardship

1. Certificate enters stewardship lifecycle.
2. Renewal, revocation, replay, and audit apply.

See [STEWARDSHIP_PROTOCOL_V1.md](./STEWARDSHIP_PROTOCOL_V1.md).

## Anti-greenwash rule

Certificates MUST remain `DRAFT` / promotion `HOLD` until all required gates pass. “Version X deployed” without a promoted certificate is not a CEF stewardship claim.
