# Governed Event Chain Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make governed-event-chain-organ-gate
python -m pytest tests/test_governed_event_chain_organ.py -q
```
