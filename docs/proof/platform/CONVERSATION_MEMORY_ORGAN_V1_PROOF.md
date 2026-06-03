# Conversation Memory Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make conversation-memory-organ-organ-gate
python -m pytest tests/test_conversation_memory_organ.py -q
```
