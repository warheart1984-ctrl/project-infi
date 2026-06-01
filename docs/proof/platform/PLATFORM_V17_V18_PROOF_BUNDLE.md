# Platform V17–V18 Proof Bundle (Workflow Marketplace)

**Claim:** Org, tenant, and curated listing visibility with install/run are **asserted**.

```bash
python .github/scripts/check-platform-marketplace-governance.py
pytest tests/test_platform_v1520.py -q -k marketplace
```
