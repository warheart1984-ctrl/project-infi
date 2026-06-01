# Cross-Machine Replay (Built, Not Active)

## Status

| Field | Value |
|---|---|
| Scaffold | **built** in repository |
| Activation | **inactive** by default |
| Claim for cross-machine acceptance | **asserted** until explicitly activated and replayed |

Cross-machine replay is wired in but deliberately disabled. Local-only evidence
remains valid for Stage 1–3 scaffolding; platform-sensitive `proven` promotion
requires activation plus second-machine evidence.

## Activation Gate

Replay runs only when **both** are true:

1. Environment variable `FORGE_CROSS_MACHINE_REPLAY_ACTIVE=1`
2. Operator has filled `docs/proof/bumblebee-forge/cross_machine/REPLAY_MANIFEST.json`
   from `REPLAY_MANIFEST.template.json`

Without activation, scripts exit with code `0` and status `inactive` (no false
`proven` claims).

## Artifacts

| Path | Purpose |
|---|---|
| `scripts/forgekeeper/cross-machine-replay.ps1` | Windows replay driver (gated) |
| `scripts/forgekeeper/cross-machine-replay.sh` | Unix replay driver (gated) |
| `docs/proof/bumblebee-forge/cross_machine/README.md` | Evidence folder guide |
| `docs/proof/bumblebee-forge/cross_machine/REPLAY_MANIFEST.template.json` | Manifest template |
| `docs/proof/bumblebee-forge/cross_machine/REPLAY_MANIFEST.json` | Filled at activation (gitignored until used) |

## Replay Command Set (when active)

```bash
py -3.12 -m unittest tests.test_forgekeeper -v
py -3.12 -m forge.forgekeeper --mode verify --plan-id <id> --scope .
py -3.12 -m forge.forgekeeper --mode chaos-check --plan-id <id> --scope .
```

Compare hashes in `REPLAY_MANIFEST.json` against local baseline in
`STAGE1_PROOF_BUNDLE.md`. Mismatches must be recorded with claim `rejected` or
`asserted` with documented reason—never silent `proven`.

## Deactivation

Unset `FORGE_CROSS_MACHINE_REPLAY_ACTIVE` or set to `0`. Remove or archive
filled manifest if replay is invalidated.

## Debt

Tracked as `BF-XM-001` in `BASELINE_CHECKLIST.md`.
