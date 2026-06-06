# Brain Session Contract v1

Status: **active contract**

CISIV stage: **structure**

## Purpose

Operator-scoped sessions for inspecting, accepting, rejecting, or deferring `brain_proposal.v1` envelopes.
Sessions record consent and ledger receipts; they never auto-execute workflow chains.

Related:

- [BRAIN_PROPOSAL_CONTRACT.md](./BRAIN_PROPOSAL_CONTRACT.md)
- Schema: [brain_session.v1.json](../../schemas/brain_session.v1.json)
- Store: [brain_session_store.py](../../src/brain_session_store.py)

## Lifecycle

```text
create session → append proposal(s) → operator decide (accept|reject|defer) → ledger receipt
```

| Status | Meaning |
|--------|---------|
| `open` | Session accepts new proposals and decisions |
| `closed` | Terminal after accept or reject |

| operator_decision | Meaning |
|-------------------|---------|
| `pending` | Awaiting operator action |
| `accepted` | Operator consented to top-ranked chain candidate |
| `rejected` | Operator declined the proposal |
| `deferred` | Operator postponed decision; session stays open |

## Authority boundary

- Accept records operator consent only
- Accept does **not** call `execute_workflow_chain`
- Reject and defer never grant execution authority
- All decisions emit `brain_proposal_decision` ledger events

## API

| Route | Purpose |
|-------|---------|
| `GET /api/operator/brain/sessions` | List sessions |
| `POST /api/operator/brain/sessions` | Create session with initial proposal |
| `GET /api/operator/brain/sessions/<id>` | Full session detail |
| `POST /api/operator/brain/sessions/<id>/propose` | Append proposal to open session |
| `POST /api/operator/brain/sessions/<id>/decide` | Accept, reject, or defer |
| `POST /api/operator/brain/sessions/<id>/deliberate` | Append deliberation trace |

Sessions MAY store `deliberations[]` and `active_deliberation_id` per [BRAIN_DELIBERATION_CONTRACT.md](./BRAIN_DELIBERATION_CONTRACT.md).
