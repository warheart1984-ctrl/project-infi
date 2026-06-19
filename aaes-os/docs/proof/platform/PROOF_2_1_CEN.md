# PROOF-2.1 Constitutional Enforcement Node

## Claim
AAES OS has a runtime primitive that intercepts proposed transitions before state mutation and produces enforcement receipts.

## Runtime Sequence
1. Proposed transition enters the CEN.
2. CEN checks requested capabilities against the runtime corridor context.
3. CEN evaluates constitutional invariants or compiled invariant DSL rules.
4. CEN returns `ALLOW` or `DENY`.
5. Allowed transitions commit to the state store.
6. Every decision produces a hash-chained enforcement receipt.

## Implemented API
- `ConstitutionalEnforcementNode`
- `createResourceFloorInvariant()`
- `compileInvariantDsl()`
- `createCenDemoResult()`

## Evidence
- Code: `packages/constitutional-enforcement-node/src/index.ts`
- Tests: `packages/constitutional-enforcement-node/src/enforcementNode.test.ts`
- Integration: `tests/integration/meta-constitutional-runtime.test.ts`
- Operator endpoint: `GET /cen/demo`
