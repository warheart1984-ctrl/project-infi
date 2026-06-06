# Brain Scoring and Sessions v1 — Proof Packet

Status: **verified by `make brain-proposal-gate`**

## Scope

1. Brain → Organ → Chain fitness rankings in `brain_proposal.v1`
2. Operator-approved Brain Sessions with accept/reject/defer and ledger receipts
3. No Cortex execution authority on accept

## Components

| Artifact | Path |
|----------|------|
| Scorer engine | `src/brain_chain_scorer.py` |
| Proposal validator | `src/brain_proposal_validator.py` |
| Session store | `src/brain_session_store.py` |
| Session schema | `schemas/brain_session.v1.json` |
| Session contract | `docs/contracts/BRAIN_SESSION_CONTRACT.md` |
| Operator UI | `frontend/src/pages/OperatorBrainSessions.jsx` |

## Verification

```bash
make brain-proposal-gate
```

Gate checks:

- `brain_proposal.v1` and `brain_session.v1` schemas parse
- Sample proposal includes sorted `organ_rankings` and `chain_rankings`
- Research intent ranks `knowledge_work` and `research_brief` highest
- ActionType and `execute: true` injections rejected
- Session create → accept emits `brain_proposal_decision` ledger event
- Pytest: `test_brain_chain_scorer`, `test_brain_session_store`, extended validator tests

## Authority boundary

- `brain_proposal.status` remains `proposal_only`
- `POST .../decide` with `accept` returns `operator_selected_chain` only
- No code path from session accept to `execute_workflow_chain`
