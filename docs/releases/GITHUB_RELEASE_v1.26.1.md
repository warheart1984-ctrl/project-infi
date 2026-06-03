# v1.26.1 — OTEM Level 10 Safe Activation

**Release 30.1** — default capability level 10; proposal-only chat; execution via workflow approvals only.

## Highlights

- `AAIS_OTEM_CAPABILITY_LEVEL` (default **10**) → `v10_governed`, deeper plans, gated auto-enqueue
- Substrate persistence **not** required for activation (phase 2 deferred)
- Stale approval guard after process restart (409 with clear operator message)

## Verification

```bash
AAIS_GENOME_BOOT=warn python -m pytest tests/test_otem_capability.py tests/test_otem_bounded_organ.py tests/test_otem_execution_approval_bridge.py tests/otem/test_otem_stabilization.py -q
```

Full notes: [docs/releases/v1.26.1-release30-1-otem-level-10-activation.md](v1.26.1-release30-1-otem-level-10-activation.md) · [CHANGELOG.md](../../CHANGELOG.md) §1.26.1
