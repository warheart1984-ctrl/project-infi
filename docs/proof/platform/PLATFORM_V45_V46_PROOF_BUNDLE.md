# Platform v45–v46 Proof Bundle (Inter-Membrane Exchange)

**Claim:** Intra-tenant listing transfer with signed envelope; peer inbound stub — **asserted**.

```bash
make platform-v45-gate
pytest tests/test_platform_v4150.py -q -k exchange
```

Includes peer outbound→inbound round-trip (`test_exchange_peer_roundtrip`) with stub transport.
