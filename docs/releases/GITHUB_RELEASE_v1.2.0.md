## Summary

AAIS **v1.2.0 — Infinity 1 · Alt-6** adds the **Adaptive Lane Organ** as the **fourteenth governed genome**. Tier 5 operator-weighted lanes wake into live runtime, merge with operator authority, and enforce lane resolution on the capability bridge.

## What's new

### Alt-6 — Adaptive Lane Organ (governed)

- `GET /api/jarvis/adaptive-lanes/status` — awakened lane registry snapshot
- Boot hook: `Tier5Governance.wake_lanes()` after Alt-4 genome validation
- Persistence: `.runtime/governance/adaptive_lanes.json`

### Fabric minimum

Five platform genes carry `operator_lanes` DNA:

- `adaptive_lane_organ`, `operator_profile_organ`, `capability_service_bridge`, `recipe_module`, `governed_direct_pipeline`

### Governance & tooling

- `make alt6-gate` — adaptive-lane + tier5 + genome
- `make alt6-governed-gate` — fabric minimum eligibility before governed promotion
- `tools/governance/alt6_promote_governed.py` — MVP → governed promotion path
- `tools/governance/check_alt6_governed_eligibility.py` — fabric minimum checker

### Runtime fixes

- Promotion health audit uses `run_gates=False` to prevent recursive gate freeze
- Bridge blocks policy-cap calls when resolved lane ≠ operator authority lane

## Upgrade

No breaking API changes. Pull `v1.2.0` and run governance gates before production use:

```bash
make alt6-governed-gate
```

## Verification

```bash
make alt6-governed-gate
make genome-gate alt4-gate tier5-gate
python -m pytest tests/test_adaptive_lane_organ.py tests/test_alt6_governed_eligibility.py \
  tests/test_adaptive_lane_bridge.py tests/test_adaptive_governance.py -q
```

**Changelog:** [CHANGELOG.md](https://github.com/warheart1984-ctrl/Project-Infinity1/blob/v1.2.0/CHANGELOG.md#120---2026-06-02--infinity-1--alt-6) · **Release doc:** [docs/releases/v1.2.0-alt6-adaptive-lanes.md](https://github.com/warheart1984-ctrl/Project-Infinity1/blob/v1.2.0/docs/releases/v1.2.0-alt6-adaptive-lanes.md)
