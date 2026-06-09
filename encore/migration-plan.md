# project-infi → Encore migration plan

**Source:** `e:\project-infi` (Python / Flask operator seam)  
**Target:** Encore.ts (`encore/`)  
**Phase:** Discover complete · Migrate in progress (1 of 6 units)

## Why Encore here

| Today (Flask) | With Encore edge |
|---------------|------------------|
| 71 `/api/operator/*` routes in one 900-line module | Services split by bounded context with generated OpenAPI |
| Untyped `jsonify({...})` responses | Request/response interfaces enforced at compile time |
| Manual infra (nginx, Docker, Appwrite sidecars) | `encore run` provisions local Postgres/Redis/etc. per service |
| Debugging via logs | Distributed traces via Encore MCP (`debug-traces` skill) |

Frontend (`frontend/`, `vercel.json`) and Python cognition runtimes stay in place. Encore absorbs the **operator product seam** incrementally.

## Out of scope

- `frontend/` — React/Vercel UI
- `src/governance_organs/*`, `aais/`, `wolf-cog-os/` — Python cognition & genome engines
- `tests/` — remain Python until each unit is migrated

## Migration units

| # | Unit | Source prefix | Endpoints | Status | Notes |
|---|------|---------------|-----------|--------|-------|
| 1 | governance-tier5 | `.runtime/governance/tier5_health.json` | 1 | **migrated** | Encore reads Python-written artifact; see `governance/tier5.ts` |
| 2 | operator-ledger | `/api/operator/ledger*` | 5 | pending | Highest-traffic accountability seam |
| 3 | operator-replay | `/api/operator/replay/*` | 1+ | pending | Depends on temporal replay store |
| 4 | operator-plugins | `/api/operator/plugins*` | 5 | pending | WorkOS RBAC on mutating routes |
| 5 | operator-organs | `/api/operator/organs*` | 6 | pending | Mesh runs need async/cron |
| 6 | operator-membranes | `/api/operator/*-membrane`, culture, identity, … | 54 | pending | Split by membrane family |

## Secrets to configure in Encore

| Secret | Purpose |
|--------|---------|
| `AAIS_REPO_ROOT` | Absolute path to project-infi (for reading `.runtime/` artifacts) |
| `WORKOS_API_KEY` | Phase 2+ when operator routes require RBAC |

## Next suggested unit

**operator-ledger** — all dependencies are file-local; no cross-unit blockers.

## Validation commands

```powershell
# Generate tier5 artifact (Python, existing)
Set-Location e:\project-infi
$env:AAIS_REPO_ROOT = "e:\project-infi"
python -c "from src.governance_organs.adaptive_engine import Tier5Governance; Tier5Governance.health_check()"

# Run Encore edge (after installing CLI)
Set-Location e:\project-infi\encore
encore secret set --dev AAIS_REPO_ROOT e:\project-infi
encore run
# GET http://localhost:4000/governance/tier5/health
```
