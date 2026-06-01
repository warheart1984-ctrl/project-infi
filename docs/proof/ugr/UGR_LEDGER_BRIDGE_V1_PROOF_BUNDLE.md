# UGR Ledger Bridge v1 Proof Bundle

**Claim:** Governed `LedgerBridge.traverse`, invariant surface INV-BRIDGE-01..08, append-only trace, TrustBundleOrgan `receive_claim` — **asserted** local.

```bash
python .github/scripts/check-ugr-ledger-bridge-governance.py
python -m pytest tests/test_ugr_ledger_bridge.py -q
```

Cross-profile parity remains on existing `make ugr-trust-bundle-gate` (UGR-D5 for cross-machine).
