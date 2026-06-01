# UGR Cogos Write-Path Proof

Claim status: **asserted** (local verification)

## Verification

```bash
make ugr-cogos-write-path-gate
```

## Artifacts

- `src/ugr/cogos_pattern_bridge.py`
- `PatternLedgerStore.append_pattern_event` / `sync_cogos_patterns`
- Mesh `POST /v1/ledger/pattern-events`, `POST /v1/ledger/cogos/sync`
