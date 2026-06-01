# Platform Membrane v1.1 Proof Bundle

| Claim | Status |
|-------|--------|
| Scoped RBAC + org isolation | **asserted** |
| Job graph + invite onboarding | **asserted** |

## Verify

```bash
make platform-v1-1-gate
pytest tests/test_platform_v11.py tests/test_platform_onboarding.py tests/test_platform_graph.py -q
```
