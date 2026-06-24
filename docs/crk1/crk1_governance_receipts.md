# CRK-1 Governance Receipts
Version 1.0

A governance receipt is a signed, replayable record that a constitutional action
was validated against the CRK-1 invariants and state machine.

Each receipt contains:

- Action metadata
- State transition
- Invariant checks
- Lineage checks
- Replay hash
- Continuity status

Programmatic issuance: `src/crk1/governance_receipt.py` → `issue_receipt(validator, context)`.

---

## Receipt Template

```
CRK-1 Governance Receipt

Action ID:        {{action_id}}
Action Type:      {{action_type}}
Submitted By:     {{identity}}
Timestamp:        {{timestamp}}

State Transition:
From:           {{from_state}}
To:             {{to_state}}
Transition OK:  {{transition_ok}}

Invariant Checks:
K0:             {{k0_status}}
K1:             {{k1_status}}
K2:             {{k2_status}}
K3:             {{k3_status}}

Lineage:
Identity:       {{identity}}
Ancestors:      {{ancestor_list}}
Evidence Used:  {{evidence_ids}}

Replay:
Outcome ID:     {{outcome_id}}
Evidence ID:    {{evidence_id}}
Replay Hash:    {{replay_hash}}

Continuity:
Status:         {{continuity_status}}

Signature:
{{signature}}
```

---

## Example Receipt (Filled)

```
CRK-1 Governance Receipt

Action ID:        8f2c1a9e
Action Type:      ExecuteDecision
Submitted By:     Identity(P)

Timestamp:        2026-06-23T23:18:00Z

State Transition:
From:           ApprovedDecision
To:             ExecutedDecision
Transition OK:  PASS

Invariant Checks:
K0:             PASS
K1:             PASS
K2:             PASS
K3:             PASS

Lineage:
Identity:       P
Ancestors:      [P]
Evidence Used:  [E1]

Replay:
Outcome ID:     O1
Evidence ID:    E2
Replay Hash:    9f8d1c3a...

Continuity:
Status:         PRESERVED

Signature:
0xA92F...F31C
```
