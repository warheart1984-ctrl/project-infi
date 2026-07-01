# Founder-Independent Governance Charter

**Authority:** SCC-1.0, GLS-1.0, GL-1.0  
**Status:** Normative — constitutional governance charter  
**Related:** [../steward-council/SCC-1.0.md](../steward-council/SCC-1.0.md), [../governance-ledger/GLS-1.0.md](../governance-ledger/GLS-1.0.md), [../ledger/GL-1.0.md](../ledger/GL-1.0.md)

## Purpose

This charter ensures the COR Suite and constitutional repository remain **founder-independent**: any qualified steward or auditor can verify state, reproduce evidence, and participate in governance without privileged access to authors or founders.

## Steward roles

| Role | Responsibility |
|------|----------------|
| **Steward** | Review COR/CSR/DRA, vote on releases and policy, record decisions in ledger |
| **Auditor** | Independently reproduce verification; may not unilaterally modify canonical spec |
| **Operator** | Run builds, regenerate observability artifacts; may not override governance decisions |

Membership rules: [SCC-1.0](../steward-council/SCC-1.0.md) — minimum 3, maximum 9 stewards; 12-month renewable terms.

## Decision authority

The Steward Council may:

- approve, reject, defer, or require fixes for releases
- authorize specification amendments
- update governance policy
- assign or revoke steward roles

The Council **may not**:

- modify canonical specification artifacts without recorded amendment
- override COR-1.0 or CSR-1.0 measurements
- declare PASS/FAIL without evidence references
- perform Proof Analysis in place of governed tooling

## Amendment process

1. Proposal recorded in governance ledger with rationale and evidence refs
2. Quorum: ⅔ of seated stewards ([SCVP-1.0](../../conformance/certification/SCVP-1.0.md))
3. Approval: ⅔ supermajority
4. Amendment artifact committed to `specification/constitutional-amendments/` or COR Suite `spec/` as appropriate
5. Regenerate observability: `npm run spec:rebuild`

## Reproduction requirements

- No release approval at **Reproduced** maturity without independent reproduction log
- Reproduction harness: [../../conformance/reproduction-harness/](../../conformance/reproduction-harness/)
- Founder-independence audit: [../../conformance/founder-independence-audit/](../../conformance/founder-independence-audit/)

Stewards must defer operational release when COR reports `proof_closure: fail` unless an explicit deferral decision is ledger-recorded with rationale.

## Conflict of interest

- Stewards must recuse from votes where they are sole author of blocking evidence
- Dual role (author + approver) requires documented exception in ledger
- No steward may suppress COR or DRA outputs

## Transparency requirements

All governance decisions must:

- append to `governance/governance-ledger/ledger.jsonl` and/or `governance/ledger/ledger.jsonl`
- include `corStateRef` or canonical commit hash in inputs
- include non-empty rationale
- be reproducible from public repository state at decision time

Public narrative must not claim correctness beyond evidence. See [Public-Messaging.md](../../conformance/cor-suite/spec/Public-Messaging.md).

## Succession and continuity

- Steward roster: `governance/ledger/stewards.json`
- Continuity checkpoints on ledger entries
- Council may appoint successors per SCC-1.0 supermajority
- No single founder key, credential, or account required to verify ledger chain

## COR Suite alignment

Governance decisions produce [governance receipts](../../conformance/cor-suite/spec/governance-receipt.schema.json) referencing:

- COR-1.0 state vector
- Optional Proof Analysis result
- Invariants enforced
- Steward signature

Analysis and observability remain strictly upstream. Governance consumes; it does not generate evidence.

## Verification

```bash
npm run audit -- ledger verify
node tools/crk.mjs validate closure
node tools/crk.mjs orc evaluate
```
