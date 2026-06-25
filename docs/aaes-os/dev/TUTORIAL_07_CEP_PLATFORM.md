# Tutorial 7 — Using the CEP Platform

## Continuity Experimental Platform

CEP enables experiment execution, logging, deterministic replay, and trace capture.

## Run an experiment

```bash
python sdk/continuity-sdk/harness/cdp1_experiment.py
```

## Logging

- Capture spans via TraceBus
- Persist runs via RunLedgerStore (in-memory today; durable ledger in Phase 6)

## Deterministic replay

After persistence lands (Phase 6), replay from ledger must produce identical receipts.

## Export continuity graphs

CDP-1 harness outputs drift metrics suitable for publication and challenge-response.
