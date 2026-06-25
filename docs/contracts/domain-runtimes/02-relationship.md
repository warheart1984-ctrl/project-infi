# Relationship runtime

## StateObjects

- **PersonState** — `person_id`, `role`, `importance`, `trust_level`, `last_contact_at`
- **RelationshipState** — `relationship_id`, `person_id`, `type` (collaborator, ally, mentor, …), `depth`, `trajectory`
- **InteractionState** — `interaction_id`, `person_id`, `date`, `channel`, `topics`, `outcomes`
- **CommitmentState** — `commitment_id`, `person_id`, `promise`, `due_at`, `status`
- **TrustSignalState** — `signal_id`, `person_id`, `direction` (earned, lost), `weight`

## Receipts

| Type | Kinds |
|------|-------|
| `InteractionReceiptV2` | Contact, Collaboration, Conflict, Repair |
| `CommitmentReceiptV2` | Create, Fulfill, Miss, Renegotiate |
| `TrustReceiptV2` | TrustEarned, TrustLost |
| `RelationshipRemediationReceiptV2` | Closure |

## Invariants

- **RR-1:** No high-importance relationship with overdue commitments.
- **RR-2:** No critical collaborator beyond `max_silence_window` without contact.
- **RR-3:** Trust changes backed by at least one `InteractionReceipt`.

## Remediation

**Trigger:** missed commitment, trust loss, prolonged silence.

**Path:** Acknowledge → Repair interaction → Update commitments → Reassess trust.

## Risk / learning / amendments

Risk: overdue commitments, trust-loss events, silence vs importance.

Learning: repair patterns reduce missed commitments and trust-loss rates.

Amendments: critical relationship definition, silence thresholds, commitment rigor by role.
