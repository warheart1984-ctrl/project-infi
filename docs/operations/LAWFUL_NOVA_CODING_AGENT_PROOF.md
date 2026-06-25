# Lawful Nova + Coding Agent — proof checklist

**Purpose:** One operator document to prove both surfaces work on `E:\project-infi`:

1. **Lawful LLM** — governed frontier model (Nemotron/OpenAI/etc.) via Nova API
2. **Agentic coding agent** — operator kernel with patch approval and workspace writes

**Canonical repo:** `E:\project-infi` only. Do not run from worktrees.

---

## What is what (avoid confusion)

| Surface | Port | Doc | Proves |
|---------|------|-----|--------|
| **Lawful LLM** | 8080 | [NOVA_LAWFUL_PRODUCTIZATION.md](../runtime/NOVA_LAWFUL_PRODUCTIZATION.md) | Real model + RSL receipts + chain contract |
| **Coding agent** | 8790 / 8791 | [operator/README.md](../operator/README.md) | `POST /agent/tasks`, patch approve, workspace files |
| AAIS / Jarvis | 8000 | [OPERATOR_GOLDEN_PATH.md](./OPERATOR_GOLDEN_PATH.md) | Dashboard + mock chat (not this proof path) |
| `/nova/coding-agent` UI | 8000 (frontend) | `frontend/src/pages/NovaCodingAgent.jsx` | Continuity studio — **not** the operator kernel |

Ungoverned AAIS `/agent/run` must stay **503** when `AAIS_UNLAWFUL_AGENTS_DISABLED=1`. The lawful coding path is **8790** only.

---

## Prerequisites

| Requirement | Check |
|-------------|--------|
| Python venv | `E:\project-infi\.venv\Scripts\python.exe` exists |
| `.novarc.ps1` | Kill switches + `NOVA_RSL_PATH` → `governance` |
| `.env` frontier keys | `NOVA_FRONTIER_PROVIDER` + provider API key (e.g. `NVIDIA_API_KEY`) |
| Services free | 8080, 8000, 8790, 8791 listening after start |

**Important:** `start-production.ps1` does **not** load `.env`. For a real frontier model, use `start-nova-for-cursor.ps1 -NoTunnel` or load `.env` into the shell before starting Nova.

### Load `.env` (PowerShell)

```powershell
cd E:\project-infi
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*([^#=]+)=(.*)$') {
    $k = $matches[1].Trim()
    $v = $matches[2].Trim().Trim('"')
    if ($k -and $v) { Set-Item "env:$k" $v }
  }
}
```

Minimum for NVIDIA Nemotron Ultra:

```env
NOVA_FRONTIER_PROVIDER=nvidia
NVIDIA_API_KEY=nvapi-...
AAIS_NVIDIA_MODEL=nvidia/nemotron-3-ultra-550b-a55b
AAIS_NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1/chat/completions
AAIS_NVIDIA_ENABLE_THINKING=1
AAIS_NVIDIA_REASONING_BUDGET=16384
```

---

## Fast path — prove everything (~5 minutes)

```powershell
cd E:\project-infi
. $env:USERPROFILE\.novarc.ps1

# Load frontier keys
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*([^#=]+)=(.*)$') {
    $k = $matches[1].Trim(); $v = $matches[2].Trim().Trim('"')
    if ($k -and $v) { Set-Item "env:$k" $v }
  }
}

# Start stacks
.\scripts\start-nova-for-cursor.ps1 -NoTunnel -FrontierProvider nvidia
.\scripts\restart-operator-stack.ps1

# Lawful LLM gates
.\.venv\Scripts\python.exe scripts\nova_productization_gate.py

# Coding agent + safety gates
.\scripts\operator_verify_all.ps1 -SkipE2e
$env:OPERATOR_E2E_SKIP_DESKTOP = "1"
.\.venv\Scripts\python.exe scripts\run_operator_e2e_validation.py
```

### Pass criteria (all must be true)

| Gate | Pass |
|------|------|
| `GET :8080/health` | `frontier_configured: true` |
| `nova_productization_gate.py` | `local_lawful_slice_ready: true` |
| `operator_red_team.ps1` | 10/10 PASS |
| `run_operator_e2e_validation.py` | 8/8 PASS |
| `POST :8000/agent/run` | HTTP **503** (unlawful path blocked) |

Reports: `.runtime\e_drive_audit.json`, `.runtime\operator_red_team.json`, `.runtime\operator_e2e_last.log`

---

## Proof A — Lawful LLM (real model)

### A1. Health

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health
```

Expect:

- `status: ok`
- `frontier_provider: nvidia` (or your provider)
- `frontier_configured: true`

If `frontier_configured: false`, Nova started without `.env` — restart with `start-nova-for-cursor.ps1 -NoTunnel`.

### A2. Governed chat (not stub cortex)

```powershell
$body = @{
  prompt     = "Say exactly: lawful llm proof ok"
  tenant_id  = "local"
  capability = "reason"
} | ConvertTo-Json

Invoke-RestMethod http://127.0.0.1:8080/v1/chat -Method POST `
  -Body $body -ContentType "application/json"
```

Expect: `text` contains the model reply; `decision` present; `chain` or receipt fields in response.

Stub mode (no frontier): responses come from deterministic Nova Cortex templates — not a failure of NVIDIA, just missing env at process start.

### A3. Productization gate

```powershell
.\.venv\Scripts\python.exe scripts\nova_productization_gate.py
```

Expect: `local_lawful_slice_ready: true` (direct LawfulLLM, chain contract, CLI health).

### A4. CLI (optional)

```powershell
. $env:USERPROFILE\.novarc.ps1
& $env:NOVA_CLI health --json
```

---

## Proof B — Agentic coding agent

Architecture: **operator kernel :8790** → **lawful brain :8791** → LawfulLLM + planner → tools (`write_patch`, etc.) with governance gate and **operator approve** before disk write.

See [operator/README.md](../operator/README.md) for patch-approval SSE sequence.

### B1. Stack health

```powershell
Invoke-RestMethod http://127.0.0.1:8790/health
Invoke-RestMethod http://127.0.0.1:8791/health
```

Expect: `lawful_brain_reachable: true` on kernel health.

### B2. Automated E2E (recommended)

```powershell
$env:OPERATOR_E2E_SKIP_DESKTOP = "1"
.\.venv\Scripts\python.exe scripts\run_operator_e2e_validation.py
```

Tests cover: task create, SSE stream, patch preview + approve, cancel, follow-up + second approve, workspace tree, desktop build skip.

**Pass:** `Summary: 8/8 passed`

### B3. Manual happy path

```powershell
# 1. Create task
$created = Invoke-RestMethod http://127.0.0.1:8790/agent/tasks -Method POST `
  -Body (@{
    goal        = "Create hello.py that prints Hello World"
    agent_id    = "builder"
    constraints = @{ read_only = $false; allow_shell = $false; max_steps = 8 }
  } | ConvertTo-Json) -ContentType "application/json"

$tid = $created.task_id

# 2. Wait for awaiting_approval (or poll GET /agent/tasks/$tid)
Start-Sleep -Seconds 8

# 3. Approve patch
Invoke-RestMethod "http://127.0.0.1:8790/agent/tasks/$tid/approve_patch" -Method POST

# 4. Confirm file
Invoke-RestMethod "http://127.0.0.1:8790/workspace/file?path=hello.py"

# 5. Follow-up
Invoke-RestMethod "http://127.0.0.1:8790/agent/tasks/$tid/message" -Method POST `
  -Body (@{ text = "Modify hello.py to print Hello Jon" } | ConvertTo-Json) `
  -ContentType "application/json"
Start-Sleep -Seconds 8
Invoke-RestMethod "http://127.0.0.1:8790/agent/tasks/$tid/approve_patch" -Method POST
Invoke-RestMethod "http://127.0.0.1:8790/workspace/file?path=hello.py"
```

**Pass:** `hello.py` contains `Hello Jon` after follow-up approve.

### B4. Red team (safety)

```powershell
.\scripts\operator_red_team.ps1 -JsonOut .runtime\operator_red_team.json
```

Confirms: lawful `POST /agent/tasks` → 200, `POST /agent/run` → 503, URG kill switch, unlawful plugs off, ForgeGate.

---

## One-shot operator verify (coding agent + safety)

```powershell
.\scripts\operator_verify_all.ps1 -RestartAais -RestartOperator
```

Includes: production audit, red team, UL smoke (57 tests), operator E2E.

Add Lawful LLM proof separately (not in `operator_verify_all` today):

```powershell
.\scripts\start-nova-for-cursor.ps1 -NoTunnel -FrontierProvider nvidia
.\.venv\Scripts\python.exe scripts\nova_productization_gate.py
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|--------|-----|
| `frontier_configured: false` | Nova started without `.env` | `start-nova-for-cursor.ps1 -NoTunnel` after loading `.env` |
| Chat returns template/stub text | No frontier provider on process | Same as above; check `/health` |
| Jarvis chat feels fake | AAIS on `--preset mock` | Expected for operator safety; use `:8080` for Lawful LLM |
| E2E tests 6–7 fail on follow-up | SSE cursor before approve events | Fixed in `run_operator_e2e_validation.py` (`_latest_event_seq`); pull latest |
| `LawfulLLM.ask() missing tenant_id` | Old lawful brain | `restart-operator-stack.ps1` after adapter fix |
| `POST /agent/run` times out | Stale AAIS without kill switch | `.\scripts\restart-aais.ps1` |
| Port 8080 bind error | Nova already running | Normal — check existing `/health` |

---

## Cursor / external clients (optional)

Cursor cannot reach `127.0.0.1`. Use tunnel + OpenAI-compatible API:

```powershell
.\scripts\start-nova-for-cursor.ps1 -FrontierProvider nvidia -NgrokDomain YOUR-SUBDOMAIN.ngrok-free.dev
```

Full steps: [lawful-nova-shell/CURSOR.md](../../lawful-nova-shell/CURSOR.md)

---

## Related docs

| Doc | Topic |
|-----|--------|
| [NOVA_LAWFUL_PRODUCTIZATION.md](../runtime/NOVA_LAWFUL_PRODUCTIZATION.md) | Lawful LLM slice status |
| [operator/README.md](../operator/README.md) | Patch approval, SSE, API routes |
| [E_DRIVE_PRODUCTION_LAYOUT.md](./E_DRIVE_PRODUCTION_LAYOUT.md) | Drive layout, ports, kill switches |
| [OPERATOR_GOLDEN_PATH.md](./OPERATOR_GOLDEN_PATH.md) | Daily AAIS operator loop |

---

## Posture label after green proof

| Label | You have |
|-------|----------|
| **Lawful LLM proven** | `frontier_configured` + productization gate + `/v1/chat` real reply |
| **Coding agent proven** | E2E 8/8 + red team 10/10 |
| **Operator production-local** | Above + `operator_verify_all` + audit PASS |

This is **local dev proof**, not hardware GA. GPU/NIM fleet evidence and cross-machine continuity bundles remain separate release gates per [NOVA_LAWFUL_PRODUCTIZATION.md](../runtime/NOVA_LAWFUL_PRODUCTIZATION.md).

**Collapsed stack roadmap:** [../architecture/COLLAPSED_STACK_V0.md](../architecture/COLLAPSED_STACK_V0.md) — constitutional substrate v0.0, rebuild order, next three moves.
