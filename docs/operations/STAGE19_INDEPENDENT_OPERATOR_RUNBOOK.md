# Stage 19 Independent Operator Runbook

Status: **active** — live federation pilot (Release 49 / FCE)

This runbook is for **real independent operators** joining a federated civilizational epoch — not mock scopes or single-substrate tests.

## Prerequisites

1. AAIS instance running with Release 49+ body symbols (`make federated-civilizational-epoch-body-gate` green on your machine)
2. Distinct `AAIS_OPERATOR_ORG_DOMAIN` per operator (must differ from witness domains)
3. Peer URLs configured: `AAIS_PEER_BASE_URLS=https://peer-b.example:8000,...`
4. Optional trust pin: `AAIS_PEER_TRUST_BUNDLE_PIN=<sha256-of-peer-bundle>`
5. Active epoch in [`governance/operator_federated_epoch_registry.v1.json`](../../governance/operator_federated_epoch_registry.v1.json) (`amendable: true`, not past `epoch_end_utc`)

## Coordination classes

| Class | Who | Action |
|-------|-----|--------|
| FCE-0 | Any peer | Observe federated epoch posture |
| FCE-1 | Proposer operator | Surface charter candidates |
| FCE-2 | Adopting operator + Jarvis + external witness | Adopt epoch charter with witness quorum |
| FCE-3 | Population fixture | Read-only population-scale observe |

## Live pilot compose (multi-substrate)

```powershell
cd e:\project-infi\deploy\pilot
docker compose -f docker-compose.federation-live.yml up --build
```

- **Alpha:** http://127.0.0.1:8000 (`operator-alpha.local`)
- **Beta:** http://127.0.0.1:8001 (`operator-beta.local`)

Each instance lists the other in `AAIS_PEER_BASE_URLS`.

## Witness adopt flow (FCE-2)

1. Seed upstream GCV civilization (Stage 18) on adopting substrate if empty
2. `POST /api/operator/federated-epochs/observe` with `{ "session_id": "...", "window_days": 7 }`
3. Pick `candidate_id` from surfaced candidates (requires amendable epoch + GCV upstream)
4. Collect ≥1 external witness with **distinct** `witness_org_domain`
5. `POST /api/operator/federated-epochs/charters/adopt`:

```json
{
  "operator_approved": true,
  "candidate_id": "<from observe>",
  "external_witnesses": [
    {
      "witness_org_domain": "witness-org.example",
      "witness_attestation": "I attest adoption under epoch_pilot_002",
      "trust_bundle_ref": "out/witness_bundle_alpha.json"
    }
  ]
}
```

6. Verify overlay in `.runtime/jarvis_memory_board_federated_epoch.v1.json` and ledger events

## Trust Bundle witness template

See [`docs/operations/templates/FCE_WITNESS_TRUST_BUNDLE.template.json`](templates/FCE_WITNESS_TRUST_BUNDLE.template.json).

## Live proof gates

```powershell
cd e:\project-infi
$env:STAGE19_REQUIRE_LIVE = "1"
python -m aais start --preset mock --data-dir ./.runtime/aais-data
make stage19-federation-gate
```

Artifacts:

- `ci-artifacts/stage19_live_federation_*.txt`
- `ci-artifacts/body_promotion_load_report.json`
- `docs/audit/STAGE19_PROOF_CYCLE_<date>.md`

## Sign-off

When all seven rungs in [`STAGE19_LIVE_PROOF_LADDER.md`](../audit/STAGE19_LIVE_PROOF_LADDER.md) are **proven**, complete [`STAGE19_LIVE_PROVEN_SIGNOFF.md`](../audit/STAGE19_LIVE_PROVEN_SIGNOFF.md) and promote body matrix row **49** to `proven`.

## Epoch rollover

When `epoch_end_utc` passes, registry curators must:

1. Set prior epoch `frozen: true`, `amendable: false`
2. Add new epoch with fresh window and set `default_epoch_id`
3. Re-run `make federated-civilizational-epoch-body-gate`

Amendments and FCE adopts are blocked outside amendable windows by design.
