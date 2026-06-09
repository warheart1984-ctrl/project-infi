# OTEM Ceiling Operator Handbook

Authority: `docs/contracts/OTEM_CEILING_RULES.md`, `schemas/otem_ceiling_rules.v1.json`

## Purpose

Level **20** is the **sovereign** constitutional recovery ceiling. Levels **16–19** are the **containment** band. Together they enforce:

1. Diagnostic bundle
2. Preview (dry-run)
3. Explicit operator decision
4. ODL closure
5. Post-decision hardening

No silent autonomous L20 recovery.

## Authority bands

| Band | Levels | Operator posture |
|------|--------|------------------|
| autonomous | 1–9 | Normal immune defend/heal/harden |
| governed | 10–15 | High immune; L10 execution-approval path |
| containment | 16–19 | Pause + diagnostic bundle |
| sovereign | 20 | Non-delegable constitutional decisions only |

Default deployment remains `AAIS_OTEM_CAPABILITY_LEVEL=10` (governed).

## Five operator decisions

| Decision | Effect |
|----------|--------|
| `rollback_to_checkpoint` | Restore checkpoint genesis; exit containment |
| `quarantine_archive` | Quarantine scope; exit containment |
| `safe_mode_reanchor` | Safe-mode reanchor; enters sovereign (L20) |
| `accept_containment` | Acknowledge containment; remain paused |
| `constitutional_amendment` | Constitutional law change; enters sovereign (L20) |

## Surfaces

| Surface | Path / command |
|---------|----------------|
| Operator UI | `/operator/ceiling` |
| Status API | `GET /api/operator/ceiling` |
| Invoke | `POST /api/operator/ceiling/invoke` |
| Preview | `POST /api/operator/ceiling/preview` |
| Apply | `POST /api/operator/ceiling/apply` |
| Console snapshot | `otem_ceiling` key on `GET /api/operator/console` (v1.3) |
| Emergency invoke | `AAIS_OTEM_CEILING_INVOKE=1` or `make otem-ceiling-invoke` |

## Recommended workflow

1. Confirm containment or trigger via invoke (audited).
2. Review diagnostic bundle ID and triggers in console snapshot.
3. **Preview** the intended decision (records ODL preview row).
4. **Apply** the same decision (records ODL decision row; runs hardening).
5. Re-check `pipeline_state` returns to `idle` unless sovereign/containment is intentionally held.

## Verification

```bash
make otem-ceiling-gate
make ugr-operator-console-gate
```

## Cross-links

- [OTEM_CEILING_RULES.md](../contracts/OTEM_CEILING_RULES.md)
- [OTEM_EXECUTION_SUBSTRATE.md](../contracts/OTEM_EXECUTION_SUBSTRATE.md)
- [UGR_OPERATOR_CONSOLE_CONTRACT.md](../contracts/UGR_OPERATOR_CONSOLE_CONTRACT.md)
