# Platform v37–v38 Proof Bundle (Mesh v3)

**Claim:** Event retention compaction and assignment queue — **asserted**.

```bash
make platform-v37-gate
pytest tests/test_platform_v3140.py -q -k mesh
```
