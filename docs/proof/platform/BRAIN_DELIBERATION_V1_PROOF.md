# Brain Deliberation v1 — Proof Packet

Status: **verified by `make brain-proposal-gate`**

## Scope

1. `brain_deliberation.v1` multi-stage reasoning protocol (options → tradeoffs → commit)
2. Adapter from internal `cognitive.deliberation` lobe
3. Composition with `brain_proposal.v1` via `deliberation_id`
4. Brain session storage and operator UI timeline

## Components

| Artifact | Path |
|----------|------|
| Schema | `schemas/brain_deliberation.v1.json` |
| Contract | `docs/contracts/BRAIN_DELIBERATION_CONTRACT.md` |
| Validator | `src/brain_deliberation_validator.py` |
| Runtime adapter | `src/brain_deliberation_runtime.py` |
| Session extension | `src/brain_session_store.py` |
| Operator UI | `frontend/src/pages/OperatorBrainSessions.jsx` |

## Verification

```bash
make brain-proposal-gate
```

Gate checks:

- `brain_deliberation.v1` schema and contract exist
- Sample deliberation builds with ordered `stage_chain`
- `execute: true` injection rejected
- Session create → deliberate → accept has no chain executor path
- Pytest: `test_brain_deliberation_validator`, `test_brain_deliberation_runtime`

## Authority boundary

- `brain_deliberation.status` remains `proposal_only`
- Deliberation endpoints never call `execute_workflow_chain`
- Commit-stage recommendation is inspectable only until operator acts separately
