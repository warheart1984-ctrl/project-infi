# Stage 19 Live Proof Ladder

Status: **active** — stricter than Stage 18 pilot sign-off

Stage 19 promotion requires **`proven`** artifacts for all seven live-federation criteria. Offline-only chaos is **insufficient** when `STAGE19_REQUIRE_LIVE=1`.

## Ladder rungs

| Rung | Criterion | Required artifact | Exit label |
|------|-----------|-------------------|------------|
| 1 | Live multi-tenant federation | `ci-artifacts/stage19_live_federation_*.txt` from federation-live compose + chaos Phase D | proven |
| 2 | Real peer diplomacy | Bilateral accord adopt with non-mock `AAIS_PEER_BASE_URLS` peer | proven |
| 3 | Body promotions under load | `ci-artifacts/body_promotion_load_report.json` within SLO | proven |
| 4 | Independent operator witnesses | ≥2 witness Trust Bundles on same NFD treaty adopt | proven |
| 5 | Sustained inter-org proof cycles | 3× `docs/audit/STAGE19_PROOF_CYCLE_<date>.md` consecutive green | proven |
| 6 | Population-scale governance | Population fixture observe report within SLO | proven |
| 7 | Epoch constitutional evolution | Completed epoch window test + live 7d pilot record | proven |

## Mandatory gates

```powershell
cd e:\project-infi
make stage19-federation-gate
```

With live AAIS:

```powershell
$env:STAGE19_REQUIRE_LIVE = "1"
python -m aais start --preset mock --data-dir ./.runtime/aais-data
python tools/stress/federation_chaos_hammer.py
python tools/stress/body_promotion_load_hammer.py
python tools/governance/run_inter_org_proof_cycle.py --witness-bundle out/
```

## Rejection rules

- **Reject** row 49 `proven` if health preflight fails and `STAGE19_REQUIRE_LIVE=1`
- **Reject** witness bundles without distinct `witness_org_domain`
- **Reject** epoch sign-off if amendment accepted outside amendable window
- Cross-machine matrix required per `REPO_PROOF_LAW.md` §Cross-Machine before final sign-off

## Sign-off

Only after all seven rungs: fill [`STAGE19_LIVE_PROVEN_SIGNOFF.md`](STAGE19_LIVE_PROVEN_SIGNOFF.md) and promote body matrix row 49 to **`proven`**.
