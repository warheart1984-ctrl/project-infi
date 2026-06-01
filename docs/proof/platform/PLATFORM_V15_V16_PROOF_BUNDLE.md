# Platform V15–V16 Proof Bundle (Operator Mesh)

**Claim:** Operator presence, assignment, on-call, and handoff are **asserted** on this machine.

```bash
python .github/scripts/check-platform-mesh-governance.py
pytest tests/test_platform_v1520.py -q -k "mesh or handoff"
```
