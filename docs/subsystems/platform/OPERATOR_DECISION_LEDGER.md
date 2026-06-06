# Operator Decision Ledger

Status: **governed**

Cross-plane accountability ledger linking pipeline turns, OTEM approvals, URG receipts, plug execution, and brain decisions.

## Scope

Each scope (session, tenant, or `global`) stores an append-only hash-chained JSONL log. Events carry causal parents, blast radius, drift context, and optional federation metadata for bilateral URG missions.

## APIs

| Route | Purpose |
|-------|---------|
| `GET /api/operator/ledger` | List events |
| `GET /api/operator/ledger/digest` | Digest counts |
| `GET /api/operator/ledger/query` | Indexed query |
| `GET /api/operator/ledger/diff` | Decision diff |
| `GET /api/operator/ledger/federation/<grant_id>/graph` | Federation graph |
| `GET /api/jarvis/operator-decision-ledger/status` | Status |

Routes register via `src/operator_api_routes.py`.

## Store

`{AAIS_RUNTIME_DIR}/operator_ledger/{scope}/events.jsonl`

## Proof and lab

- Governed proof: `docs/proof/platform/OPERATOR_DECISION_LEDGER_GOVERNED_PROOF.md`
- Lab scenarios A–E: `docs/proof/platform/OPERATOR_DECISION_LEDGER_LAB_GUIDE.md`

## Gates

```bash
make operator-decision-ledger-gate
make operator-decision-ledger-v2-graph-gate
```
