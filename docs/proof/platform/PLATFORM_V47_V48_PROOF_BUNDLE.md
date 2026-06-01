# Platform v47–v48 Proof Bundle (Platform Ledger v2)

**Claim:** Hash-chained ledger append, query, verify, CLI export — **asserted**.

```bash
make platform-v47-gate
pytest tests/test_platform_v4150.py -q -k ledger
python -m platform ledger export --org led-org
```

Ledger kinds `audit.event`, `usage.rollup`, and `mesh.*` are mirrored when store-backed audit and mesh/usage writers run.
