# UGR Cogos Write-Path Contract (UGR-D4)

Authority: `docs/contracts/PATTERN_LEDGER_SCHEMA_V0_5.md`

## Scope

Unifies Wolf CoG pattern writes into the AAIS unified ledger:

- `src/ugr/cogos_pattern_bridge.py` — normalize + idempotent ingest
- `PatternLedgerStore.append_pattern_event()` — UGR facade
- `PatternLedgerStore.sync_cogos_patterns()` — fixture/batch sync
- Mesh: `POST /v1/ledger/pattern-events`, `POST /v1/ledger/cogos/sync`
- Detachment guard routes through `PatternLedgerStore`

Cogos canonical local files remain; unified ledger receives normalized `pattern_event` rows with `origin: cogos`.

## Verification

```bash
make ugr-cogos-write-path-gate
```

Evidence: `docs/proof/ugr/UGR_COGOS_WRITE_PATH_PROOF.md`
