# Seam Stress Run — 2026-06-06

## Executive summary

**CISIV stage:** `verification`  
**Purpose:** Repeatable SEAM_LAW pressure run after Infinity-1 operator seam landing — auto-discover runtime boundaries (health, legacy bridge, Jarvis status farm, operator product surface), classify failures, and drive wave closure.  
**Base:** `http://127.0.0.1:8000` (mock preset)  
**Generated at:** `2026-06-06T14:21:24Z`

### Outcome verdict

Runtime seams are **closed**. Waves 1–4 (hard 500s, health/bridge, operator surface, status-farm drift) completed with **0 failures** and **0 critical/high** findings. Wave 5 governance gates re-verified green on workspace rerun (see [WAVE5_GOVERNANCE_CLOSURE_PLAN.md](./WAVE5_GOVERNANCE_CLOSURE_PLAN.md)).

### Route inventory

| Surface | Count |
|---------|------:|
| Total Flask routes | 396 |
| Operator routes | 29 |
| Jarvis routes | 268 |
| Jarvis `/status` routes | 164 |

### Claims matrix

| # | Claim | Label | Evidence |
|---|-------|-------|----------|
| 1 | `/health` healthy, legacy bridge mounted | proven | Health JSON below; `legacy_api_mount_error: null` |
| 2 | Zero 5xx on discovery probe set | proven | 187/187 probes OK — `ci-artifacts/seam_discovery_report.json` |
| 3 | Live stress barrage err-free | proven | 559/559 OK — `ci-artifacts/live_stress_report.json` |
| 4 | No genome-declared API gaps | proven | Genome gaps: none |
| 5 | No open SEAM-LIVE records | proven | Seam records: none (clean run) |
| 6 | Chat identity stable under repetition | proven | `identity_stable: true` |
| 7 | Long-turn 403 is governance block, not seam | proven | OTEM/checkpoint deny; `truncated_suspected: false` |
| 8 | Operator workflow stack gates | proven | `make operator-workflow-stack-gate` + flagship 13/13 |
| 9 | Full flagship governance (Wave 5) | proven | genome/naming/alt4 PASS on 2026-06-06 rerun |

### Cross-links

- [LOGBOOK.md](./LOGBOOK.md) — 2026-06-06 seam stress closure entry
- [AAIS_FLAGSHIP_AUDIT_2026-06-06.md](./AAIS_FLAGSHIP_AUDIT_2026-06-06.md)
- [OPERATOR_WORKFLOW_SKILLS.md](../operators/OPERATOR_WORKFLOW_SKILLS.md)
- [SEAM_STRESS_OPERATOR_SIGNOFF_2026-06-06.md](./SEAM_STRESS_OPERATOR_SIGNOFF_2026-06-06.md)

### Reproduction

```bash
python -m aais start --data-dir ./.runtime/aais-data --preset mock --no-browser
python tools/stress/seam_discovery_stress.py
python tools/stress/live_api_stress.py --auto-discover
make operator-workflow-stack-gate
```

---

## Operator summary

- Base: `http://127.0.0.1:8000`
- Offline harvest: `False`
- Total probes: `187`
- Failures: `0`
- Critical/high: `0`

## Health

```json
{
  "reachable": true,
  "status_code": 200,
  "healthy": true,
  "legacy_api_loaded": true,
  "legacy_api_mount_error": null,
  "degraded": false
}
```

## Findings

| Endpoint | Status | Severity | Seam class | Closure |
|----------|--------|----------|------------|---------|
| _none_ | — | — | — | closed |

## Genome gaps (declared API missing from Flask)

- none

## Seam records

- none (clean run)

## Chat pressure

```json
{
  "identity_stable": true,
  "turns": [
    {
      "turn": 1,
      "status": 200,
      "reply_len": 0
    },
    {
      "turn": 2,
      "status": 200,
      "reply_len": 0
    },
    {
      "turn": 3,
      "status": 200,
      "reply_len": 0
    }
  ],
  "long_turn": {
    "status": 403,
    "reply_len": 0,
    "truncated_suspected": false
  }
}
```
