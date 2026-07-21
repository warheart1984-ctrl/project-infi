# Sovereign Router X Product Architecture Specification

**Release family:** CRK-1 companion specification  
**Purpose:** Product architecture for the constitutional orchestration layer that selects reasoning engines, enforces routing policy, and preserves evidence continuity.

---

## 1. Scope

Sovereign Router X is the orchestration product that sits above model execution. It is not the model, and it is not the customer-facing end goal by itself. Its job is to:

- accept a minimal request packet
- evaluate constitutional and operational policy
- select the reasoning engine
- record the route decision as evidence
- pass the scoped packet to the selected engine
- ingest the reply into the durable runtime
- expose receipts, replay, and traceability to the operator

## 2. Product intent

The product is designed to make reasoning provider-neutral and constitutionally traceable.

Sovereign Router X provides:

- policy-controlled routing
- request minimization
- model selection
- evidence recording
- ledger update support
- replayability
- billing-grade usage accounting
- domain profile support

## 3. Non-goals

Sovereign Router X does not:

- redefine CIS Core terminology
- execute the reasoning model itself
- own the customer's source of truth
- replace the durable ledger
- bypass validation or evidence capture
- collapse routing policy into model prompts

## 4. Architectural layers

| Layer | Responsibility | Primary artifacts |
|------|-----------------|------------------|
| Customer surface | User input, status, receipts, billing view | Web app, console, API client |
| Orchestration layer | Build packet, choose route, attach policy | `tools/codex-handoff-orchestrator.ts`, `tools/codex-handoff-router.ts` |
| Router layer | Select engine and route policy | Sovereign Router X package |
| Reasoning layer | Produce bounded reply | Codex or another compatible model |
| Validation layer | Schema, policy, and evidence checks | Handoff schemas and ingest validator |
| Ledger layer | Persist request, reply, route, and receipts | Task ledger and replay store |
| Billing layer | Meter usage and compute charges | Subscription and usage accounting |
| Research OS layer | Capture evidence, insights, ideas, and actions | Research OS corpus and proof surface |

## 5. Runtime contract

Every routed task should produce the following minimum record set:

- request packet
- route decision
- selected model
- backend family
- reply packet
- validation result
- ledger entry
- evidence receipt
- replay record

## 6. Request flow

1. A user submits a task.
2. The app converts it into a minimal request packet.
3. Sovereign Router X evaluates the packet and selects the engine.
4. The orchestrator sends the packet to the selected engine.
5. The reply is validated against the reply schema.
6. The runtime records the route and the reply in the ledger.
7. Evidence and billing counters are updated.
8. The customer receives a traceable receipt.

## 7. Domain profile model

The product supports implementation profiles without changing constitutional requirements.

Planned profiles include:

- Government
- Healthcare
- Finance
- Research
- Education
- Infrastructure
- Regenerative Intelligence

Profiles may change:

- routing policy
- retention settings
- evidence thresholds
- billing shape
- display terminology

Profiles may not change:

- CIS Core terminology
- constitutional requirements
- proof requirements
- replay requirements
- traceability requirements

## 8. Evidence and proof surfaces

Each execution should be able to answer:

- what request was routed
- why that route was chosen
- what engine was selected
- what reply was produced
- what evidence supports the decision
- what tests verify the behavior
- how the record replays

## 9. Repository mapping

| Product concern | Repo anchor |
|----------------|-------------|
| Packet creation | `tools/codex-handoff-prompt.ts` |
| Packet validation | `tools/codex-handoff-cli.ts`, `tools/codex-handoff-ingest.ts` |
| Route decision | `tools/codex-handoff-router.ts` |
| End-to-end orchestration | `tools/codex-handoff-orchestrator.ts` |
| Smoke verification | `tools/codex-handoff-smoke.ts` |
| Route tests | `tests/release/codex-handoff-router.test.ts` |
| Router package | `packages/sovereignx-router/` |
| Evidence and traceability | `packages/aaes-governance/` |

## 10. Acceptance criteria

Sovereign Router X is considered product-complete for this slice when:

- request packets are minimal and schema-validated
- route decisions are recorded before replay ingestion
- reply validation blocks malformed output
- the ledger stores both the reply and the route decision
- short and long packets select different reasoning surfaces when policy requires it
- smoke tests pass end to end
- the architecture is documented and traceable

