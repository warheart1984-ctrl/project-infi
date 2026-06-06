# Operator Decision Ledger Lab Guide (Scenarios A–E)

## Prerequisites

```bash
export AAIS_RUNTIME_DIR=.runtime/lab-odl
make operator-decision-ledger-gate
make operator-decision-ledger-v2-graph-gate
```

## Scenario A — Pipeline emit → digest

```bash
curl -s "http://127.0.0.1:5000/api/operator/ledger/digest?session_id=lab-a"
```

Expected: `entry_count` increases after a governed chat turn emits `pipeline_turn`.

## Scenario B — OTEM approval join

1. Create OTEM handoff in session with `AAIS_OTEM_CAPABILITY_LEVEL=10`.
2. Approve via `/workflows/approvals`.
3. Query ledger:

```bash
curl -s "http://127.0.0.1:5000/api/operator/ledger/query?session_id=<session>&kind=otem_approval"
```

Expected: `pending` row followed by `approve` or `reject` with causal parent.

## Scenario C — URG mission receipt

Run governance mutation mission; verify `urg_receipt` kind:

```bash
curl -s "http://127.0.0.1:5000/api/operator/ledger?session_id=tenant:acme"
```

## Scenario D — Federation digest graph

```bash
curl -s "http://127.0.0.1:5000/api/operator/ledger/federation/<grant_id>/graph?session_id=tenant:acme"
```

Expected: `home_nodes`, optional `peer_nodes`, `digest_verified` boolean.

## Scenario E — Replay ↔ ledger deep link

1. Open `/operator/replay/operator_session/<session_id>`.
2. Scrub timeline; click **Open in Operator Ledger**.
3. Ledger scope matches session id; digest counts align with replay chips.
