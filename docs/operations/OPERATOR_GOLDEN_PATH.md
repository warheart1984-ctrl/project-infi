# Operator golden path — daily cockpit

Status: **asserted** (consolidates existing onboarding; verify gates for **proven**)

One document for **first run**, **early-adopter posture**, and **daily operation**. Deep dives stay in linked guides.

---

## Philosophy

From [EARLY_ADOPTER_CHARTER.md](./EARLY_ADOPTER_CHARTER.md): **Knowledge is freely given. Trust is earned.** Run gates, record sign-off, report seams.

From [STABILIZE_AND_FREE.md](../spine/STABILIZE_AND_FREE.md): stabilize law and verification first; then reduce operator cognitive load.

---

## Path A — First run (10 minutes, mock)

### 1. Bootstrap

**Windows (recommended):**

```powershell
.\scripts\start-infinity1.ps1
```

**Manual (any OS):** follow [FIRST_TIME_OPERATOR_GUIDE.md](./FIRST_TIME_OPERATOR_GUIDE.md) Tier 1.

### 2. Verify healthy

```bash
curl -fsS http://127.0.0.1:8000/health
python -m tools.ul.smoke
```

Healthy when `/health` succeeds and a chat turn returns `ul_substrate`, `law_enforcement`, and `cisiv_stage`.

### 3. Open surfaces

| Surface | URL |
|---------|-----|
| Operator dashboard | http://127.0.0.1:8000/operator |
| Jarvis console | http://127.0.0.1:8000/app/jarvis |
| Workflow approvals | http://127.0.0.1:8000/workflows/approvals |

---

## Path B — Infinity Pilot (Docker, ~15 minutes)

Follow [INFINITY_PILOT_EARLY_ADOPTER.md](./INFINITY_PILOT_EARLY_ADOPTER.md):

```bash
cd deploy/pilot && cp .env.example .env
docker compose up --build -d
python ../../scripts/pilot_compose_smoke.py --base-url http://127.0.0.1:8090 --api-key <your-key>
```

Posture label: **Pilot** when `make stack-pilot-gate` is green ([charter](./EARLY_ADOPTER_CHARTER.md)).

---

## Daily operator — 3 screens, 3 actions

Use this loop once AAIS or Pilot stack is up.

| # | Screen | URL | What to read |
|---|--------|-----|--------------|
| 1 | **Seam health** | `/operator` or `GET /api/operator/dashboard/seam-health` | Stress summary, health probe, workflow stack gate list |
| 2 | **Approvals** | `/workflows/approvals` | OTEM L10 pending items — no bypass for governed execution |
| 3 | **Brain / ledger** | Operator dashboard `brain` + `ledger_digest` panels | `proposal_only` proposals; read-only ledger digest |

| # | Action | Command or surface |
|---|--------|-------------------|
| 1 | **Confirm runtime** | `curl -fsS http://127.0.0.1:8000/health` |
| 2 | **Clear or defer approvals** | Workflow approvals UI — accept/reject with reason |
| 3 | **Weekly gate spot-check** | `make civilizational-arc-smoke` (fast) or `make infinity1-flagship-verification` (full) |

Dashboard contract: [INFINITY1_OPERATOR_DASHBOARD_CONTRACT.md](../contracts/INFINITY1_OPERATOR_DASHBOARD_CONTRACT.md)  
Panel guide: [GOVERNANCE_DASHBOARD_OPERATOR_GUIDE.md](../operators/GOVERNANCE_DASHBOARD_OPERATOR_GUIDE.md)

---

## Posture labels (honest)

| Label | You have… |
|-------|-----------|
| **Exploring** | Mock/laptop preset, learning surfaces |
| **Pilot** | Docker compose + `stack-pilot-gate` green |
| **GA-ready (claimed)** | Production gates + [OPERATOR_GA_REVIEW_PROTOCOL.md](./OPERATOR_GA_REVIEW_PROTOCOL.md) sign-off |
| **Production (your org)** | Your SLOs, backups, on-call |

---

## Verification ladder

| When | Gate |
|------|------|
| After doc-only change | `make civilizational-arc-smoke` |
| After operator/dashboard change | Mock start + operator URLs in PR |
| After Platform/Pilot change | `make stack-pilot-gate` |
| Before claiming GA posture | `make infinity1-flagship-verification` |

Baseline reference: [INFINITY1_FLAGSHIP_VERIFICATION_BASELINE_2026-06-08.md](../proof/platform/INFINITY1_FLAGSHIP_VERIFICATION_BASELINE_2026-06-08.md)

---

## Cross-links

| Doc | Purpose |
|-----|---------|
| [FIRST_TIME_OPERATOR_GUIDE.md](./FIRST_TIME_OPERATOR_GUIDE.md) | Tier 1–3 depth, subsystems |
| [EARLY_ADOPTER_CHARTER.md](./EARLY_ADOPTER_CHARTER.md) | Trust model, what we ask |
| [INFINITY_PILOT_EARLY_ADOPTER.md](./INFINITY_PILOT_EARLY_ADOPTER.md) | Full-stack Docker pilot |
| [AAIS_PRODUCTION_OPERATOR_RUNBOOK.md](./AAIS_PRODUCTION_OPERATOR_RUNBOOK.md) | Production tiers A/B/C |
| [OPERATOR_WORKFLOW_SKILLS.md](../operators/OPERATOR_WORKFLOW_SKILLS.md) | Workflow families + OTEM |
| [HELP_WANTED_HUB.md](../community/HELP_WANTED_HUB.md) | Co-builder entry |

---

## Imagine Generator (optional)

Set `STORY_FORGE_XAI_API_KEY` or `XAI_API_KEY` before start for Grok render paths. Check `GET /api/jarvis/imagine/keys-status`.
