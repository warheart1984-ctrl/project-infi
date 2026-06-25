# Domain runtime facades (Stratum 3)

**Status:** spec + Pydantic scaffold (`domain_runtimes/`). **Wired client:** Operator (`operator_task`) only.

Each runtime is a **view** on the constitutional substrate — not a separate state machine:

- `StateObject` + universal transition graph (Article XV)
- Domain-specific `*ReceiptV2` kinds → `TransitionReceiptV2` via CSR
- Append-only evidence in `.runtime/receipts/`
- Observer packets on terminal / remediation closure

## Runtimes

| Runtime | Spec | Package module | Invariant prefix |
|---------|------|----------------|------------------|
| Personal continuity | [01-personal-continuity.md](./01-personal-continuity.md) | `domain_runtimes.personal_continuity` | PC- |
| Relationship | [02-relationship.md](./02-relationship.md) | `domain_runtimes.relationship` | RR- |
| Cognitive | [03-cognitive.md](./03-cognitive.md) | `domain_runtimes.cognitive` | CR- |
| Founder | [04-founder.md](./04-founder.md) | `domain_runtimes.founder` | FR- |
| Opportunity | [05-opportunity.md](./05-opportunity.md) | `domain_runtimes.opportunity` | OR- |
| Reputation | [06-reputation.md](./06-reputation.md) | `domain_runtimes.reputation` | RRp- |
| Burnout | [07-burnout.md](./07-burnout.md) | `domain_runtimes.burnout` | BR- |

## Replication pattern (from Operator)

1. Register `StateObject` at create (`state_type` = domain object type).
2. On domain event → emit domain `*ReceiptV2` + `TransitionReceiptV2`.
3. `append_receipt()` + `CSR.apply_transition()`.
4. On closure / remediation → `write_observer_packet_for_task()` (or domain-named packet dir).

See [COLLAPSED_STACK_V0.md](../../architecture/COLLAPSED_STACK_V0.md).
