# AAIS Production Operator Runbook

**Audience:** operators running Project Infinity 1 like a real production service — on a laptop, a VM, Docker Compose, or Kubernetes.

**Charter:** [EARLY_ADOPTER_CHARTER.md](./EARLY_ADOPTER_CHARTER.md) — knowledge is freely given; trust is earned through verification.

**Shorter path:** [AAIS Operator Guide](../operators/AAIS_OPERATOR_GUIDE.md) (install only) · [FIRST_TIME_OPERATOR_GUIDE.md](./FIRST_TIME_OPERATOR_GUIDE.md) (tiered onboarding)

---

## 1. Choose your deployment tier

| Tier | Stack | When to use |
|------|-------|-------------|
| **A — AAIS only** | `python -m aais start` on one host | Dev, demo, single-operator executive runtime |
| **B — Pilot compose** | `deploy/pilot/docker compose` | Platform membrane + Postgres + AAIS + UGR overlay |
| **C — K8s pilot** | Helm chart under `deploy/helm/` | Multi-tenant isolation proof, NetworkPolicy, resource limits |

All tiers share the same **governance gates**; tier C adds `plat-pilot-k8s-gate`.

---

## 2. Prerequisites (production-minded)

| Item | Minimum |
|------|---------|
| OS | Linux, macOS, or Windows 10+ with Python 3.10+ |
| RAM | 8 GB (pilot compose); 16 GB recommended for default preset |
| Disk | 10 GB free for images, data dir, and logs |
| Network | Outbound HTTPS only if using cloud LLM providers |
| Secrets | `.env` from `.env.example` — never commit real keys |

Optional: Docker 24+ and Compose v2 (tier B/C), `kubectl` + cluster (tier C), Node 18+ (rebuild frontend).

---

## 3. Tier A — AAIS standalone (production hygiene)

### 3.1 Install

```bash
git clone https://github.com/warheart1984-ctrl/Project-Infinity1.git
cd Project-Infinity1
python -m pip install -e ".[dev]"
cp .env.example .env
```

Edit `.env` for providers you use. For dry runs without keys:

```bash
python -m aais prepare --data-dir ./.runtime/aais-data
python -m aais doctor --data-dir ./.runtime/aais-data
python -m aais start --data-dir ./.runtime/aais-data --preset mock --no-browser
```

### 3.2 Health checks (every deploy)

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/api/operator/dashboard/seam-health
curl -fsS http://127.0.0.1:8000/api/operator/dashboard/monitoring
```

Expect HTTP 200 and JSON with `status` / panel keys documented in the Infinity-1 operator dashboard contract.

### 3.3 Operator surfaces (bookmark these)

| Surface | URL | Purpose |
|---------|-----|---------|
| Operator dashboard | http://127.0.0.1:8000/operator | Seam health, monitoring alerts, Infinity-1 snapshot |
| Plugins + Organs | http://127.0.0.1:8000/operator/plugins | Skill libraries, workflow bundles |
| Brain sessions | http://127.0.0.1:8000/operator/brain | Proposals, deliberation, accept/reject |
| Decision ledger | http://127.0.0.1:8000/operator/ledger | Governed decision graph |
| Workflow approvals | http://127.0.0.1:8000/workflows/approvals | OTEM Level 10 execution gate |
| Jarvis console | http://127.0.0.1:8000/app/jarvis | Executive chat (proposal-only lane) |

### 3.4 OTEM Level 10 (governed execution)

Default: `AAIS_OTEM_CAPABILITY_LEVEL=10`. Chat proposes; **workflow approvals** execute.

1. Run a task in Jarvis that emits a workflow handoff.
2. Open `/workflows/approvals` in the **same API process** that handled the turn.
3. Approve or reject — do not restart the server between handoff and approve (substrate is in-memory until persistence phase 2).

Check posture:

```bash
curl -s http://127.0.0.1:8000/legacy_api/api/jarvis/otem-bounded/status | python -m json.tool
```

### 3.5 Verification gates (run before calling it production)

On Linux/macOS with `make`:

```bash
make production-hardening-gate
make operator-workflow-stack-gate
make infinity1-flagship-verification
make ga-signoff-gate
```

On Windows (PowerShell), same gates via Python:

```powershell
python .github/scripts/check-production-hardening.py
python tools/governance/run_infinity1_flagship_verification.py
python .github/scripts/check-ga-signoff.py --mode fail
python -m pytest tests/test_wave6_transition_seams.py -q
```

Record results and complete [OPERATOR_GA_REVIEW_PROTOCOL.md](./OPERATOR_GA_REVIEW_PROTOCOL.md) if you claim GA-ready posture.

---

## 4. Tier B — Full pilot stack (Platform + UGR + AAIS)

### 4.1 Bootstrap

```bash
cd deploy/pilot
cp .env.example .env
# Set PLATFORM_MASTER_API_KEY to a strong random value
docker compose up --build -d
```

### 4.2 Smoke the stack

```bash
python scripts/pilot_compose_smoke.py --base-url http://127.0.0.1:8090 --api-key <your-master-key>
```

| Service | URL |
|---------|-----|
| AAIS UI | http://127.0.0.1:8000 |
| Platform API | http://127.0.0.1:8090 |
| Platform console | http://127.0.0.1:8090/platform (if frontend built) |

### 4.3 Org and API keys

1. `POST /v1/orgs` with master key header `X-Api-Key`.
2. `POST /v1/orgs/{org_id}/api-keys` for operator-scoped key.
3. Set `ugr_tenant_id` on the org for cognition overlay reads.

### 4.4 MA-13 operator rules (non-negotiable)

- **Autopilot** — policy-bound routing only; start with `mode=dry_run`.
- **Jarvis** — executive for cognition; Platform observes and actuates ops jobs.
- **Sovereign export** — `POST /v1/orgs/{id}/sovereign/export-pack` for audit + ledger + usage ZIP.

### 4.5 Pilot verification

```bash
make stack-pilot-gate
```

This includes: platform v6 gates, UGR ledger bridge, pilot compose smoke, production hardening, and K8s isolation script checks.

---

## 5. Tier C — Kubernetes

1. Install chart from `deploy/helm/` per [PLATFORM_K8S_ISOLATION_PROOF.md](../proof/platform/PLATFORM_K8S_ISOLATION_PROOF.md).
2. Apply NetworkPolicy, Secret, ServiceAccount, and resource limits as shipped in chart values.
3. Run isolation smoke:

```bash
python scripts/k8s_tenant_isolation_smoke.py
make plat-pilot-k8s-gate
```

---

## 6. Monitoring and incident response

### 6.1 Infinity-1 dashboard

Open `/operator` and confirm:

- **Seam health** — stress-run probes and seam labels green.
- **Monitoring alerts** — sentinel and Cloud Forge rail status (contract v1.1 `monitoring` key).

API mirrors:

- `GET /api/operator/dashboard/seam-health`
- `GET /api/operator/dashboard/monitoring`

### 6.2 Logs and ledger

- Platform audit: JSONL append-only under pilot data volume.
- Ledger verify: `GET /v1/orgs/{id}/ledger/verify`
- AAIS run ledger: `GET /api/jarvis/run-ledger/status`

### 6.3 Kill switch

1. Stop workers / `docker compose down` or scale deployments to zero.
2. Revoke API keys at Platform (`DELETE` key endpoints).
3. Set autopilot to dry-run or disable witness paths per [OPERATIONAL_RUNBOOK.md](../subsystems/platform/OPERATIONAL_RUNBOOK.md).

### 6.4 Rollback

- **Compose:** `docker compose down`; restore Postgres volume from snapshot.
- **AAIS only:** stop process; restore `./.runtime/aais-data` from backup.
- **Helm:** `helm rollback <release> <revision>`.

---

## 7. Release and upgrade procedure

1. Pull tagged release or `main` at a known commit.
2. Run full gate block (section 3.5 + `stack-pilot-gate` if using pilot).
3. `python -m aais doctor --data-dir <path>` after dependency changes.
4. Rebuild frontend only if you changed `app/frontend`: `npm run build` in frontend dir, then `python -m aais prepare`.
5. Document commit SHA and gate output in your operator logbook.

Evidence bundle for GA closure: [PRODUCTION_GA_SIGNOFF_2026-06-06.md](../audit/PRODUCTION_GA_SIGNOFF_2026-06-06.md).

---

## 8. Customer / compliance deliverables

| Artifact | How |
|----------|-----|
| Usage CSV | `GET /v1/orgs/{id}/usage?format=csv` |
| Sovereign pack | Console or `POST .../sovereign/export-pack` |
| Ledger chain | `GET .../ledger/verify` + `python -m platform ledger export` |
| UGR cognition overlay | `GET .../ledger/cognition-overlay` (read-only) |
| Seam stress reproduction | [SEAM_STRESS_RUN_2026-06-06.md](../audit/SEAM_STRESS_RUN_2026-06-06.md) |

---

## 9. Known limits (honest debt)

See [INFINITY_PILOT_BASELINE_CHECKLIST.md](../baseline/INFINITY_PILOT_BASELINE_CHECKLIST.md):

- PLAT-D8 — OIDC IdP integration partial.
- UGR-D5 — cross-machine trust matrix open.
- OTEM substrate — cross-restart approval durability deferred (phase 2).

Claim **production** only with your org's sign-off, not because the repo says GA-ready.

---

## 10. Escalation and support

- SLA orientation: [INFINITY_PILOT_SLA_ORIENTATION.md](./INFINITY_PILOT_SLA_ORIENTATION.md)
- Constitutional violations (MA-13 class): platform ops owner + constitutional review
- Upstream issues: GitHub repository issues with gate output and commit SHA

---

## Quick reference — one page

```bash
# Start (mock, no browser)
python -m aais start --data-dir ./.runtime/aais-data --preset mock --no-browser

# Health
curl -fsS http://127.0.0.1:8000/health

# Production gates (Unix)
make production-hardening-gate stack-pilot-gate wave6-transition-gate infinity1-flagship-verification ga-signoff-gate

# Pilot stack
cd deploy/pilot && docker compose up --build -d
python scripts/pilot_compose_smoke.py --base-url http://127.0.0.1:8090 --api-key $KEY
```

**Trust is earned:** run the commands, save the output, sign your review.
