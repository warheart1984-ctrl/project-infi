# First-Time Operator Guide

This is the consolidated onboarding path for Project Infinity / AAIS. It stitches together the README quick start, Infinity Pilot Docker bootstrap, and pointers to advanced subsystems.

**Running like production?** Read [EARLY_ADOPTER_CHARTER.md](./EARLY_ADOPTER_CHARTER.md) and follow [AAIS_PRODUCTION_OPERATOR_RUNBOOK.md](./AAIS_PRODUCTION_OPERATOR_RUNBOOK.md) after Tier 1 — knowledge is freely given; trust is earned through gates and sign-off.

For constitutional law and proof requirements, see the root README governance section. For subsystem depth, follow links at the end.

---

## Before You Start

### Prerequisites

| Tier | Requirements |
|---|---|
| **Tier 1** | Python 3.10+, Git |
| **Tier 2** | Tier 1 + Docker 24+, Compose v2, 8 GB RAM recommended |
| **Tier 3** | Tier 2 + familiarity with Makefile gates and subsystem docs |

Optional everywhere: Node.js 18+ (rebuild frontend), Redis (Celery worker), provider API keys.

**Imagine Generator (Grok render):** To use `POST /api/jarvis/imagine/grok-render` or the capability bridge action `imagine_generator` / `grok_render`, set `STORY_FORGE_XAI_API_KEY` (preferred) or `XAI_API_KEY` in the environment before starting AAIS. Keys are read only from env — never from request bodies. Check readiness with `GET /api/jarvis/imagine/keys-status`.

### Presets

| Preset | Use when |
|---|---|
| `mock` | No GPU / no API keys — deterministic local replies |
| `laptop` | Lightweight real local model path |
| `default` | Full runtime (may load heavier local models) |

### What "healthy" looks like

1. `curl -fsS http://127.0.0.1:8000/health` returns success.
2. A chat turn returns `ul_substrate`, `modular_preview`, `law_enforcement`, and `cisiv_stage` on the payload.
3. UL smoke passes: `python -m tools.ul.smoke`

---

## Tier 1: Run AAIS Locally (10 minutes)

### 1. Clone and install

```bash
git clone https://github.com/warheart1984-ctrl/Project-Infinity1.git
cd Project-Infinity1
python -m pip install -e ".[dev]"
cp .env.example .env
# Edit .env only if you need OpenAI / Anthropic / OpenRouter routes
```

### 2. Prepare runtime data

```bash
python -m aais prepare --data-dir ./.runtime/aais-data
python -m aais doctor --data-dir ./.runtime/aais-data
```

`prepare` stages the packaged UI into `app/static/`. A prebuilt bundle ships with the repo.

### 3. Start AAIS

```bash
python -m aais start --data-dir ./.runtime/aais-data --preset mock --no-browser
```

Developer alternative: `make run` (uvicorn on `:8000`).

### 4. Open surfaces

| Surface | URL |
|---|---|
| Health | http://127.0.0.1:8000/health |
| Operator dashboard | http://127.0.0.1:8000/operator |
| App shell | http://127.0.0.1:8000/app |
| Jarvis console | http://127.0.0.1:8000/app/jarvis |
| Workflow approvals | http://127.0.0.1:8000/workflows/approvals |
| Jarvis API | `/legacy_api` (Flask, bridged through FastAPI) |

### 5. Verify with curl

```bash
curl -fsS http://127.0.0.1:8000/health

curl -fsS -X POST http://127.0.0.1:8000/legacy_api/api/chat/sessions \
  -H "Content-Type: application/json" \
  -d "{\"system_prompt\":\"You are Jarvis.\"}"

# Use session_id from response:
curl -fsS -X POST http://127.0.0.1:8000/legacy_api/api/chat/sessions/<session_id>/message \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Summarize AAIS.\",\"response_mode\":\"operator\"}"
```

### 6. UL governance smoke

```bash
python -m tools.ul.drift
python -m tools.ul.smoke
python -m pytest tests/test_cisiv.py tests/test_chat_turn_governance.py tests/test_forge_repo_governance.py -q
```

### Optional contractor lanes

Start only when you need forge/evolve features:

| Service | Port | Env var |
|---|---|---|
| Forge | 6060 | `FORGE_BASE_URL` |
| ForgeEval | 6061 | `FORGE_EVAL_BASE_URL` |
| EvolveEngine | 6062 | `EVOLVE_BASE_URL` |

Without contractors, core chat works; explicit forge routes error until the service is up.

---

## Tier 2: Infinity Pilot Docker (15 minutes)

Governed full stack: **Platform Membrane** (ops) + **UGR** (cognition/proof) + **AAIS/Jarvis** (executive).

### Bootstrap

```bash
cd deploy/pilot
cp .env.example .env
# Edit PLATFORM_MASTER_API_KEY and other secrets — do not use defaults in production
docker compose up --build -d
python ../../scripts/pilot_compose_smoke.py --base-url http://127.0.0.1:8090 --api-key <your-key>
```

| Surface | URL |
|---|---|
| AAIS UI | http://127.0.0.1:8000 |
| Platform API | http://127.0.0.1:8090 |
| Platform console | `/platform` (if frontend built) |

### Org and API key

1. `POST /v1/orgs` with master key (`X-Api-Key`).
2. `POST /v1/orgs/{org_id}/api-keys` for operator key.
3. Map `ugr_tenant_id` on org for cognition overlay reads.

### Verify stack gate

```bash
make stack-pilot-gate
```

### Customer-facing rules (MA-13)

- **Autopilot** is policy-bound routing only; use `mode=dry_run` first.
- **Jarvis** remains cognition executive; Platform observes and actuates ops jobs.
- **Sovereign export pack** delivers audit + ledger + usage ZIP for compliance review.

Full early-adopter detail: [INFINITY_PILOT_EARLY_ADOPTER.md](./INFINITY_PILOT_EARLY_ADOPTER.md).

Known limits: not GA — see [INFINITY_PILOT_BASELINE_CHECKLIST.md](../baseline/INFINITY_PILOT_BASELINE_CHECKLIST.md).

---

## Tier 3: Advanced Subsystems

Use these after Tier 1 or Tier 2. Each subsystem has its own runbook; this section is a pointer matrix only.

| Subsystem | Entry | Notes |
|---|---|---|
| **Wolf-CoG-OS ISO forge** | [wolf-cog-os/forge/README.md](../../wolf-cog-os/forge/README.md), root `Makefile` (`make rootfs`, `make iso-tree`) | Outputs under `wolf-cog-os/output/` (local-only, gitignored) |
| **Platform membrane** | [docs/subsystems/platform/ONBOARDING.md](../subsystems/platform/ONBOARDING.md) | Multi-tenant ops, ledger, artifacts on `:8090` |
| **Forge contractors** | `forge/`, `forge_eval/`, `evolve_engine/` | HTTP lanes on ports 6060–6062 |
| **UGR** | `src/ugr/`, UGR trust bundle gates in CI | Cognition/proof overlay; pairs with Platform |
| **Scorpion** | [docs/subsystems/scorpion/OPERATIONAL_RUNBOOK.md](../subsystems/scorpion/OPERATIONAL_RUNBOOK.md) | OS anomaly extractor — runbook is a skeleton |
| **Mechanic** | [mechanic/HOSTED_PILOT.md](../../mechanic/HOSTED_PILOT.md) | Hosted repo scan service |
| **AI Factory / Lab** | `ai_factory/`, `lab/` | Factory specs and lab CLI |

Authority reminder: Jarvis (`src/api.py`) owns cognition; Platform is ops ingress only.

Integration map: [FULL_STACK_PILOT_INTEGRATION.md](./FULL_STACK_PILOT_INTEGRATION.md).

### OTEM Level 10 (execution via approvals)

OTEM is **activated at capability level 10** by default (`AAIS_OTEM_CAPABILITY_LEVEL=10` in `.env`).

| Step | Action |
|---|---|
| 1 | Run OTEM in Jarvis with a task that produces a **workflow handoff** (proposal-only in chat). |
| 2 | Open **Workflow Approvals**: http://127.0.0.1:8000/workflows/approvals (or the Dashboard handoff link when pending). |
| 3 | **Approve** or **reject** the OTEM execution item in the **same API process** that handled the OTEM turn. |

Chat never executes tools or applies patches directly. Roll back to v5-frozen posture with `AAIS_OTEM_CAPABILITY_LEVEL=5` (disables auto-enqueue).

**After restart:** Pending approvals may be stale if the in-memory substrate workflow was lost. Reject the stale row and re-run the OTEM handoff, or approve before restarting the server.

Contract: [OTEM_EXECUTION_SUBSTRATE.md](../contracts/OTEM_EXECUTION_SUBSTRATE.md).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `cp .env.example .env` fails | Wrong directory | Run from repo root; template is at `.env.example` |
| Health OK but chat errors on forge routes | Contractor not running | Start forge/evolve service or avoid forge routes |
| Empty or generic replies with `default` preset | Missing local models / keys | Use `--preset mock` or set provider keys in `.env` |
| Pilot smoke fails | Wrong API key or compose not up | Check `deploy/pilot/.env`, `docker compose ps` |
| UI missing after clone | Skipped `aais prepare` | Run `python -m aais prepare --data-dir ./.runtime/aais-data` |

Stop foreground runtime with `Ctrl+C`. Do not delete `.runtime/aais-data` during active sessions.

---

## Security Before Production

Read [SECURITY.md](../../SECURITY.md) before any internet-facing deployment.

1. Rotate all Platform secrets in `deploy/pilot/.env` or `deploy/platform/.env`.
2. Generate fresh CoGOS trust keys — never use development signing keys from local backup bundles.
3. Keep provider API keys in `.env` or your secret manager, not in git.
4. Set `APP_BEARER_TOKEN` if exposing the workflow shell beyond localhost.
5. Treat compose placeholder secrets (`mechanic-secret`, `minioadmin`) as local-dev only.

---

## Next Reading

1. [AAIS_PRODUCTION_OPERATOR_RUNBOOK.md](./AAIS_PRODUCTION_OPERATOR_RUNBOOK.md) — production tiers, gates, rollback
2. [EARLY_ADOPTER_CHARTER.md](./EARLY_ADOPTER_CHARTER.md) — early adopter philosophy
3. [README.md](../../README.md) — architecture and governance summary
4. [docs/README.md](../README.md) — documentation map
5. [docs/runtime/AAIS_RUNTIME_GUIDE.md](../runtime/AAIS_RUNTIME_GUIDE.md) — runtime handbook
6. [docs/runtime/AAIS_SUBSYSTEM_SPEC.md](../runtime/AAIS_SUBSYSTEM_SPEC.md) — subsystem status map
7. [CHANGELOG.md](../../CHANGELOG.md) — release history
