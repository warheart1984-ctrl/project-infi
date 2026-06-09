# Governance dashboard — operator guide

Status: **proven** (structure aligned with [INFINITY1_OPERATOR_DASHBOARD_CONTRACT.md](../contracts/INFINITY1_OPERATOR_DASHBOARD_CONTRACT.md))

~30-minute read. Screenshots optional.

---

## Purpose

The governance dashboard is the **read-only cockpit** at `/operator`. It aggregates seam health, brain readouts, ledger digest, workflow stack status, and monitoring alerts. It **never mutates runtime** (`runtime_effect: readout_only`).

---

## Surfaces

| Surface | Path | Use |
|---------|------|-----|
| Full dashboard | http://127.0.0.1:8000/operator | Primary UI |
| Console snapshot | `GET /api/operator/console` → key `infinity1` | Programmatic poll |
| Seam health | `GET /api/operator/dashboard/seam-health` | Lightweight stress poll |
| Monitoring | `GET /api/operator/dashboard/monitoring` | Sentinel / rail alerts |

Backend: `src/operator_infinity1_dashboard.py`  
Frontend: `frontend/src/pages/OperatorConsole.jsx`

---

## Snapshot keys (`infinity1`)

| Key | Meaning | When to escalate |
|-----|---------|------------------|
| `health` | Live `/health` or seam artifact fallback | Non-200 or missing substrate fields |
| `seam_stress` | Summary from `ci-artifacts/seam_discovery_report.json` | Rising stress counts after deploy |
| `live_stress` | `ci-artifacts/live_stress_report.json` | Live probe failures |
| `ledger_digest` | Read-only operator decision ledger aggregate | Unexpected digest gaps |
| `brain` | Session aggregates — **proposal_only** | Any execute/authorize signal in fixtures |
| `plugins` | Plug adapter registry counts | Missing expected Story Forge / media routes |
| `workflow_stack` | Static gate manifest + seam closure claim | Gate list out of date vs Makefile |
| `quick_links` | Deep links to operator surfaces | — |
| `monitoring` | Sentinel + Cloud Forge rail + mesh poll | Active alerts |

---

## Civilizational posture fields

When civilizational arc metadata is present on contributions or pods, discovery and reputation surfaces may show **High** or **Civilizational** arc tiers (10× pod reward multiplier per [discovery README](../proof/discovery/README.md)). The dashboard reflects **observed** posture from ledger and seam artifacts — not marketing labels.

For arc-specific smoke after deploy:

```bash
make civilizational-arc-smoke
```

Evidence: [CO_BUILDER_CIVILIZATIONAL_ARC_SMOKE_V1_PROOF.md](../proof/platform/CO_BUILDER_CIVILIZATIONAL_ARC_SMOKE_V1_PROOF.md)

---

## Somatic / seam health

1. Open `/operator` — review seam stress panel.
2. If live probe unavailable, dashboard falls back to committed `ci-artifacts/seam_discovery_report.json`.
3. Regenerate offline stress locally:

```bash
python tools/stress/seam_discovery_stress.py --offline
```

4. Compare before/after deploy; file an issue with reproduction if seams diverge from contract.

---

## Daily verification (after deploy)

```bash
curl -fsS http://127.0.0.1:8000/health
pytest tests/test_operator_infinity1_dashboard.py tests/test_ugr_operator_console.py -q
make civilizational-arc-smoke
```

For GA posture claims, also run `make infinity1-flagship-verification` and complete [OPERATOR_GA_REVIEW_PROTOCOL.md](../operations/OPERATOR_GA_REVIEW_PROTOCOL.md).

---

## Escalation

| Symptom | Action |
|---------|--------|
| Dashboard 5xx | Check AAIS logs; run `python -m aais doctor` |
| Seam stress spike | Run seam discovery stress; attach artifact to issue |
| Brain panel shows non-proposal authority | **Stop** — treat as seam violation; cite [SEAM_LAW.md](../contracts/SEAM_LAW.md) |
| Monitoring alerts | [INFINITY_PILOT_SLA_ORIENTATION.md](../operations/INFINITY_PILOT_SLA_ORIENTATION.md) |

---

## Cross-links

- [OPERATOR_GOLDEN_PATH.md](../operations/OPERATOR_GOLDEN_PATH.md) — daily 3 screens / 3 actions
- [AAIS_OPERATOR_GUIDE.md](./AAIS_OPERATOR_GUIDE.md) — full operator guide
- [FIRST_TIME_OPERATOR_GUIDE.md](../operations/FIRST_TIME_OPERATOR_GUIDE.md) — first run
- [INFINITY1_OPERATOR_DASHBOARD_V1_PROOF.md](../proof/platform/INFINITY1_OPERATOR_DASHBOARD_V1_PROOF.md) — proof packet

---

## Co-builder issue

Delivered for [Help Wanted #4](https://github.com/warheart1984-ctrl/Project-Infinity1/issues/4) (governance dashboard operator guide).
