# E:\ drive — production layout

**Canonical repo (only place to run software):** `E:\project-infi`

Everything else on the drive is a **git worktree snapshot**, **tooling**, **docs**, or **archive**.

## Audit snapshot (2026-06-22)

Last run: `.\scripts\e_drive_production_audit.ps1` → **PASS** (warnings only).

| Check | Status |
|-------|--------|
| Nova / AAIS / operator / brain HTTP | PASS |
| `local_lawful_slice_ready` + `local_services_ready` | PASS |
| Unlawful plugs (30) | OFF |
| `aris/` legacy folder | Removed (was hygiene ERROR) |
| `ci-artifacts/` | WARN — local CI outputs; safe to delete when idle |
| Git worktrees on E: | WARN — use only `project-infi` |
| forge/evolve contractors (6060–6062) | WARN — optional unless full forge stack |

Report JSON: `.runtime\e_drive_audit.json`

## Operator verification (audit + red team + smoke + E2E)

One command after code or config changes:

```powershell
.\scripts\operator_verify_all.ps1 -RestartAais -RestartOperator
```

| Script | What it proves |
|--------|----------------|
| `e_drive_production_audit.ps1` | Ports, health, productization gates, unlawful plugs off |
| `operator_red_team.ps1` | Lawful task path, AAIS `/agent/run` blocked, URG frozen, ForgeGate |
| `tools.ul.smoke` | 57 UL/ForgeGate pytest tests |
| `run_operator_e2e_validation.py` | Patch approve, cancel, follow-up, workspace tree |

Reports: `.runtime\e_drive_audit.json`, `.runtime\operator_red_team.json`, `.runtime\operator_e2e_last.log`

**Full merged proof checklist (Lawful LLM + coding agent):** [LAWFUL_NOVA_CODING_AGENT_PROOF.md](./LAWFUL_NOVA_CODING_AGENT_PROOF.md)

Restart helpers (safe: only kills `python` listeners, not `wslrelay`):

```powershell
.\scripts\restart-aais.ps1
.\scripts\restart-operator-stack.ps1
```

## Quick start (Windows)

```powershell
cd E:\project-infi
.\scripts\start-production.ps1
```

Daily inspection (no guessing):

```powershell
.\scripts\e_drive_production_audit.ps1
.\scripts\e_drive_production_audit.ps1 -JsonOut .runtime\e_drive_audit.json
```

## Directory map

| Path | Role | Use it? |
|------|------|---------|
| `project-infi\` | **Canonical AAIS + Lawful Nova** | **Yes** — `.venv`, APIs, operator UI |
| `lawful-shell-wt\` | Worktree `llm-nova-shell` | **No** — stale snapshot |
| `nova-runtime-wt\` | Worktree `feat/cvr-lawful-turn` | **No** — merge then archive |
| `urg-wt\` | Worktree `feat/nova-in-urg` | **Merge-only** — URG/NeoMundi experiments |
| `mcps\` | Local MCP descriptors | Reference; not production runtime |
| `.cursor\` | Workspace MCP override | Empty `mcpServers` for lawful workspace |
| `Voss Standalone\` | Empty folder | Remove or extract `Voss Standalone.zip` |
| Drive-root `*.pdf` / `*.zip` | Specs & backups | Archive — not runtime |

## Ports (healthy production)

| Port | Service | Required? |
|------|---------|-----------|
| 8080 | Lawful Nova API | Yes |
| 8000 | AAIS (Jarvis / operator) | Yes |
| 8790 | Operator kernel | When using governed coding agent |
| 8791 | Lawful brain | With operator kernel |
| 3000 | Frontend proxy | Optional |
| 6060–6062 | forge / evolve contractors | Optional (WARN if down in mock) |

## Safety posture

`%USERPROFILE%\.novarc.ps1` should set:

- `NOVA_RSL_PATH` → `E:\project-infi\governance` (not `nova\`)
- `AAIS_UNLAWFUL_AGENTS_DISABLED=1` — blocks **ungoverned** AAIS `/agent/run`, plug-class agents (`cursor_skill`, `hf_agent_skill`, `mcp`); does **not** block lawful operator kernel (`8790`)
- `URG_MISSION_KILL_SWITCH=1`, `URG_EXECUTION_MODE=DRY_RUN` — URG composite missions frozen until you lift kill switch

Unlawful plug classes are off in `.runtime/plug_adapter/enabled_plugs.json`.

### Lawful agentic coding (Nova operator)

| Surface | Port | Status with current flags |
|---------|------|---------------------------|
| Operator kernel tasks | 8790 `POST /agent/tasks` | **Lawful** — governance gate + patch approval |
| Lawful brain planner | 8791 | Required by operator kernel |
| Nova API chat | 8080 | **Lawful** — direct LawfulLLM |
| AAIS `/agent/run` | 8000 | **Blocked** when `AAIS_UNLAWFUL_AGENTS_DISABLED=1` |

### URG / UGR (Unified Governed Runtime)

Mission switchboard in `src/ugr/`, `deploy/ugr/` — **not** the same as operator kernel. With kill switch + `DRY_RUN`, new URG missions do not execute live. See `docs/URG_CLOUD_PLATFORM.md`. Experimental FOS wire: `E:\urg-wt\` (do not run from there).

## Worktree rule

Only `E:\project-infi` has `.venv` and current kill switches. Do not run Python or APIs from the other worktrees.

## Related

- [OPERATOR_GOLDEN_PATH.md](./OPERATOR_GOLDEN_PATH.md)
- [FIRST_TIME_OPERATOR_GUIDE.md](./FIRST_TIME_OPERATOR_GUIDE.md)
- [NOVA_LAWFUL_PRODUCTIZATION.md](../runtime/NOVA_LAWFUL_PRODUCTIZATION.md)
