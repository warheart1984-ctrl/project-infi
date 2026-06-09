# URG Epistemic State Contract (v1)

Canonical 3-state epistemic layer over 4-band Library Standing.

## States

| `epistemic_state` | 4-band standing | `claim_label` | Library | Operator promotion |
|---|---|---|---|---|
| `rejected` | `denied` | `denied` / `rejected` | No | Never |
| `pending` | `hypothetical`, `asserted` | `hypothetical`, `asserted` | Yes | No |
| `proven` | `proven` | `proven` | Yes | Yes (governed bridge) |

## Envelope

All governed receipts and promotion records SHOULD carry an `EpistemicStateEnvelope` (`schemas/epistemic_state.v1.json`):

- `epistemic_state`
- `standing`
- `claim_label`
- optional `rejection_source`
- optional `falsity_fingerprint`
- optional `pod_id`, `contribution_id`
- optional `promoted_to_operator`, `promotion_event_id`

## Rejection sources

| `rejection_source` | Origin |
|---|---|
| `discovery_denial` | Proof promotion `deny:*` rules |
| `falsity_registry` | RLS falsity ledger |
| `mesh_falsity` | Mesh gossip falsity adapter |
| `operator_override` | Explicit operator reversal with evidence |
| `manual` | Manual governance action |

Rejected claims MUST NOT silently re-enter operator knowledge. Promotion and chat read paths consult `FalsityRegistry.is_resurrection_blocked()`.

## Operator bridge

Proven URG receipts auto-promote through `src/urg_operator_knowledge_bridge.py`:

1. Read catalog via `ContributionDiscoveryStore`
2. Filter by `epistemic_state`
3. On `pod_proven`, write operator memory (`category: urg_proven`, `source: urg_library`)
4. Append idempotent promotion ledger (`.runtime/urg_operator_promotions.jsonl`)
5. Emit ODL `urg_knowledge_promotion` event

Manual promotion: `POST /api/operator/knowledge/promote-from-urg`

## Chat parity

URG library context follows the same metadata + `prompt_block` pattern as workspace and live research:

- Turn prep stores `session.metadata["urg_library_context"]`
- `conversation_memory.build_messages()` injects the block
- `prompt_assembly.py` registers `urg_library_context` singleton block
