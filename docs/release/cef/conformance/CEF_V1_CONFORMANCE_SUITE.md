# CEF v1.0 Conformance Test Suite

**Status:** Specified — executable later via `packages/cef-core` / CI  
**Parent:** [../CEF_V1_SPECIFICATION.md](../CEF_V1_SPECIFICATION.md)

## 1. Core CEF conformance

### Test CEF-01: Core schema validation

**Goal:** All evidence objects validate against `cef-core-evidence.schema.json`.

### Test CEF-02: Invariant enforcement

**Goal:** No promotion when required fields are missing or verification checks fail.

### Test CEF-03: Replay determinism

**Goal:** Given an evidence object, replay instructions reconstruct the same inputs and verification path.

## 2. OEL profile conformance

### Test OEL-01: Deployment evidence completeness

**Goal:** All required OEL fields present for a deployment.

### Test OEL-02: Security gate enforcement

**Goal:** Promotion blocked if SBOM or vulnerability scan is missing or failing.

### Test OEL-03: Policy validation

**Goal:** NetPol, RBAC, and securityContext must be validated before promotion.

### Test OEL-04: Certificate DRAFT behavior

**Goal:** Baseline Certificate v1.0 remains DRAFT/HOLD until all gates pass.

## 3. Certification Engine conformance

### Test CE-01: Authority binding

**Goal:** Promotion requires a valid CAR with appropriate scope.

### Test CE-02: Immutable certificate

**Goal:** Once promoted, certificate fields cannot be modified.

### Test CE-03: Promotion traceability

**Goal:** Every certificate has a corresponding promotion decision record (CDR).

## 4. Stewardship conformance

### Test ST-01: State transitions

**Goal:** Certificates move only through allowed states  
(`unpromoted` → `active` → `renewal_pending` → `revoked` → `historical`).

### Test ST-02: Revocation evidence

**Goal:** Revocation always produces a revocation evidence record.

### Test ST-03: Historical replay

**Goal:** Historical certificates remain replayable with their original context.

## Fixtures

| Fixture | Path |
| --- | --- |
| Baseline DRAFT certificate | `docs/release/operational-evidence-layer/certificates/baseline-v1.0.certificate.yaml` |
| Core schema | `docs/release/cef/schemas/cef-core-evidence.schema.json` |
| OEL schema | `docs/release/cef/schemas/cef-oel-evidence.schema.json` |
