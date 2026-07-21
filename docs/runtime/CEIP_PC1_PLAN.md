# CEIP Production Candidate PC-1

Status: implementation program; not yet achieved.

PC-1 is earned only when every mandatory gate below has reproducible evidence. “Implemented” means fresh automated verification exists; “independently verified” requires a separate implementation or reviewer and cannot be self-attested by the reference runtime team.

## Workstreams and gates

| Workstream | Required deliverables | Acceptance evidence | Current state |
|---|---|---|---|
| Persistence | workflow/event/object repositories, transactional outbox, event store, snapshots, idempotency, locks, retries, DLQ, event migrations | concurrency tests, crash/recovery tests, migration/replay receipts | Not implemented |
| Service layer | HTTP and optional gRPC APIs, OIDC, RBAC, tenant isolation, secrets/config, health/readiness, OTel | API conformance, authz negatives, tenant-isolation tests, trace sample | Not implemented |
| Reliability | stale approval, chaos/failure injection, load/scaling, concurrent replay, DR, backup/restore | measured reports with environment, thresholds, raw results | Not implemented |
| Security | threat model, signed packages/receipts, verification, SBOM/provenance, supply-chain controls, review, penetration test | signed artifacts, scan reports, review and remediation receipts | Not implemented |
| Independent validation | second implementation, interoperability, deterministic replay, certification, evidence verification | cross-runtime fixture results and independent attestation | Not implemented |
| Operator experience | Twin Console connected to live runtime with all 19 stages, objects, evidence, approvals, receipts, replay, conformance, admission, audit | end-to-end browser/API demonstration and event/object receipts | Reference UI only |

## Implementation order

1. Freeze fixtures and compatibility tests for canonical CEIP contracts.
2. Implement transactional persistence and outbox behind repository interfaces.
3. Expose authenticated HTTP APIs with tenant and workflow version enforcement.
4. Connect the Twin Console to those live APIs and canonical event stream.
5. Add signing, verification, threat controls, SBOM, and supply-chain gates.
6. Run concurrency, stale-approval, failure, load, replay, backup, and restore programs.
7. Build the independent implementation and execute shared fixtures.
8. Capture the full 19-stage demonstration and issue the PC-1 candidate receipt.

## PC-1 release decision

The release decision is fail-closed. Any missing mandatory evidence leaves the status at `PRE-PC1`. Passing unit tests or producing specifications alone cannot satisfy persistence, security, reliability, live-operation, or independent-validation gates.
