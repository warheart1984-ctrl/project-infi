# Pilot GA Hardening Checklist (v1.26.1)

Authority: [2026-06-05-flagship-v1.26.1-readiness.md](../trust_bundles/2026-06-05-flagship-v1.26.1-readiness.md)

## Backend verification (2026-06-05 — proven)

| Check | Command | Status |
|-------|---------|--------|
| Full pytest | `python -m pytest -q` | proven (1911 passed baseline) |
| Genome gate | `python tools/governance/check_subsystem_genome.py` | proven (179 genomes) |
| Naming-genome gate | `python tools/governance/check_naming_genome.py --snapshot` | proven (0 warnings) |
| OTEM persistence phase 2 | `python -m pytest tests/test_otem_execution_approval_bridge.py -q` | proven (7 passed) |
| UGR admission gates | `make ugr-discovery-gate ugr-rewards-gate ugr-mission-gate` | proven (32+ tests) |
| Cross-machine matrix | `python tools/proof/run_flagship_cross_machine_matrix.py --compare` | proven |
| Doctor | `python -m aais doctor --data-dir ./.runtime/pilot-ga-check` | run per operator host |

## Security closeout (2026-06-05 — proven hygiene)

| Item | Action | Status |
|------|--------|--------|
| OpenRouter key hygiene | `powershell -File tools/ops/rotate-openrouter-key.ps1 -VerifyOnly` — no key in `.env`/env | **proven** (`.runtime/pilot-ga-openrouter-verify.log`) |
| Secret scan | `git grep -i "sk-or-"` — no live keys in tracked files | **proven** |
| OpenRouter key apply + revoke | Create key in dashboard, `-NewKey`, smoke, revoke prior | **pending operator** (only when OpenRouter routing enabled) |
| JWT/session secrets | Rotate `JWT_SECRET` / session keys on production hosts | operator verify |
| Dependency audit (API) | `pip audit` or governed lockfile review | operator verify |

## Frontend / mobile re-verification (2026-06-05 — proven)

Host: Windows native Node v24.16.0 / npm 11.13.0.

```bash
cd frontend && npm ci && npm run test:ci && npm run build && npm run audit:prod
cd ../mobile && npm ci && npm run typecheck && npm audit --omit=dev
```

| Surface | Result | Log |
|---------|--------|-----|
| Frontend tests | 30 passed (8 files) | `.runtime/pilot-ga-frontend-v1.log` |
| Frontend build | exit 0 | `.runtime/pilot-ga-frontend-v1.log` |
| Frontend audit:prod | 3 vulns (axios, react-router) — exit 1 | `.runtime/pilot-ga-frontend-v1.log` |
| Mobile typecheck | exit 0 (restored `mobile/src/lib/api.ts`) | `.runtime/pilot-ga-mobile-v1.log` |
| Mobile audit | 3 vulns (axios, ws, brace-expansion) — exit 1 | `.runtime/pilot-ga-mobile-v1.log` |

Prior baseline (2026-04-29): frontend 47 passed, 0 vulns; mobile typecheck pass.

## Pilot GA acceptance criteria

- [x] Single-machine ship gate green
- [x] Governance test harness bootstrap
- [x] UGR subsystem admission (genomes + law wrappers)
- [x] OTEM persistence phase 2
- [x] SSP linguistic closure wave (193 → 0 warnings)
- [x] OpenRouter hygiene verified (no live keys; no key configured)
- [x] Frontend/mobile re-run on pilot host with Node available
- [ ] Full pytest cross-host on independent physical machine
- [ ] Production npm audit debt cleared (axios/react-router/ws)

## Claim posture

Pilot GA operator verification: **proven** on this workspace (logs archived). Production security rotation when OpenRouter is enabled and npm audit remediation: **asserted** until operator completes remaining rows.
