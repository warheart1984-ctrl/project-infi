# Seven Invariants

Governance backbone for every cognitive cycle:

1. **Traceability** — every step has `traceId`, `stepId`, audit trail
2. **Integrity of State** — span/step state machine is consistent
3. **Identity & Auth** — `actorId` required and non-empty
4. **Scope & Boundaries** — `request.scope` present and valid
5. **Explainability Hook** — steps and traces can be summarized (ULS)
6. **Reversibility / Failsafe** — action results signal rollback where possible
7. **Governance First** — invariants run before side effects proceed

Formal RFC mapping (INV-1..7): [docs/contracts/AAES_OS_V1_FORMAL_SPEC.md](../../../docs/contracts/AAES_OS_V1_FORMAL_SPEC.md) §7.

Interface reconciliation: [docs/contracts/AAES_OS_INTERFACE_V1.md](../../../docs/contracts/AAES_OS_INTERFACE_V1.md) §7.4.

Default enforcement in this starter: `src/governance/invariants.ts` (`DefaultInvariantEngine`).
