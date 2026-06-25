# Connect Lawful Nova to Cursor

Use this guide when you want **Cursor Agent** (or any OpenAI-compatible client) to call your local **Lawful Nova** API, optionally backed by **NVIDIA Nemotron Ultra** on NIM.

## Why this is different from `nova local`

Cursor routes custom-model requests through **its cloud backend**. A base URL of `http://127.0.0.1:8080` from your machine is **not** reachable from Cursor’s servers. You need:

1. Nova’s OpenAI-compatible API running on your PC (`/v1/chat/completions`, `/v1/responses`, `/v1/models`)
2. A **public HTTPS tunnel** (ngrok or Cloudflare) to that port
3. Cursor **Override OpenAI Base URL** pointed at `https://<tunnel-host>/v1`

Lawful Nova still enforces RSL receipts and governance on every turn; the frontier model (Nemotron) is optional but recommended for Agent quality.

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| **project-infi** checkout | NVIDIA frontier uses `src/providers/` in the parent repo — not standalone shell-only install |
| **Python 3.10+** + venv | `python -m venv .venv` then `pip install -e ".[dev]"` from **repo root** |
| **Cursor Pro** | Custom OpenAI base URL + Agent mode |
| **ngrok** (or cloudflared) | Reserved domain recommended for stable Cursor settings |
| **NVIDIA API key** | From [build.nvidia.com](https://build.nvidia.com) — store in `.env`, never commit |

## 1. Configure environment

From **project-infi root**, copy `.env.example` to `.env` and set:

```env
NOVA_FRONTIER_PROVIDER=nvidia
NVIDIA_API_KEY=nvapi-...your-rotated-key...
AAIS_NVIDIA_MODEL=nvidia/nemotron-3-ultra-550b-a55b
NOVA_NVIDIA_ENABLE_THINKING=true
NOVA_NVIDIA_REASONING_BUDGET=8192
```

Rotate any key that was pasted into chat or logs.

## 2. Start Nova + tunnel (one command)

**PowerShell (recommended on Windows):**

```powershell
cd E:\project-infi
.\scripts\start-nova-for-cursor.ps1 -FrontierProvider nvidia -NgrokDomain YOUR-SUBDOMAIN.ngrok-free.dev
```

From the shell package (same script, delegates to repo root):

```powershell
.\lawful-nova-shell\scripts\start-nova-for-cursor.ps1 -FrontierProvider nvidia -NgrokDomain YOUR-SUBDOMAIN.ngrok-free.dev
```

**Useful flags:**

| Flag | Purpose |
|------|---------|
| `-SkipChatProbe` | Skip slow Nemotron chat probe at startup |
| `-ChatProbeTimeoutSec 180` | Longer probe timeout (Nemotron can be slow) |
| `-NoTunnel` | API only on localhost (for local curl tests, not Cursor) |
| `-Tunnel cloudflared` | Use Cloudflare tunnel instead of ngrok |
| `-Port 8081` | If 8080 is taken (e.g. by CockroachDB) |

The script prints exact **Cursor settings** when the tunnel is up.

## 3. Configure Cursor

Open **Cursor Settings → Models → OpenAI API Key** (or “Override OpenAI Base URL”):

| Setting | Value |
|---------|--------|
| **Override OpenAI Base URL** | `https://YOUR-SUBDOMAIN.ngrok-free.dev/v1` |
| **API key** | `local-nova` (placeholder — Nova does not validate this locally) |
| **Model** | `lawful-nova` or `nvidia/nemotron-3-ultra-550b-a55b` |

Enable the model in the model list. Use **Agent** mode for tool-using workflows.

**If connection fails:** try **Settings → Network → HTTP/1.1** (some ngrok + HTTP/2 combinations fail from Cursor’s cloud).

## 4. Verify before chatting

**Quick health (local):**

```powershell
.\scripts\verify-nova-local.ps1
# or
.\lawful-nova-shell\scripts\verify-nova-local.ps1
```

Expect:

- `health status=ok`
- `frontier nvidia / nvidia/nemotron-3-ultra-550b-a55b` when `NVIDIA_API_KEY` is set
- `/v1/models` lists `lawful-nova`

**Manual check:**

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health
```

`frontier_configured: true` means Nemotron is wired; `false` means stub/deterministic cortex only.

**Response headers** on completions:

- `X-Lawful-Nova-Frontier: active` — frontier provider answered
- `X-Lawful-Nova-Frontier: stub` — local deterministic path (no frontier or missing key)
- `X-Lawful-Nova-Receipt` — signed governance receipt JSON

## 5. Shell helpers (optional)

After bootstrap, PowerShell profile exposes:

| Command | Action |
|---------|--------|
| `novcursor` | Start Nova + tunnel for Cursor (forwards args to bootstrap script) |
| `novverify` | Read-only local diagnostics |
| `novsec` | JSON health snapshot via CLI |

Bash (`source lawful-nova-shell/setup/novrc.sh`):

| Command | Action |
|---------|--------|
| `novcursor` | Prints guidance (tunnel script is Windows-first; use ngrok manually on Unix) |
| `novverify` | Runs verify script when on Windows/WSL with PowerShell |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `frontier_configured: false` | Set `NVIDIA_API_KEY` in `.env`; restart with `start-nova-for-cursor.ps1` (script force-loads Nova env keys) |
| Cursor “connection failed” | Confirm tunnel URL in browser/ngrok inspector (`http://127.0.0.1:4040`); use HTTPS `/v1` suffix; try HTTP/1.1 |
| `127.0.0.1` in Cursor | Won’t work — must use public tunnel URL |
| 404 from NVIDIA on `lawful-nova` | Fixed in provider layer — use latest code; model alias maps to Nemotron id |
| 500 “event loop” errors | Fixed — API uses sync frontier invoke inside FastAPI |
| Bootstrap WARN on chat probe | Nemotron is slow; use `-SkipChatProbe` or `-ChatProbeTimeoutSec 180` |
| Port 8080 in use | `-Port 8081` or stop conflicting service |
| Testing ngrok URL from same PC | Local TLS to ngrok may fail; trust Cursor + ngrok inspector instead |

## API surface (OpenAI-compatible)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness + frontier status |
| GET | `/v1/models` | Lists `lawful-nova`, Nemotron alias |
| POST | `/v1/chat/completions` | Chat Completions (+ `stream: true` SSE) |
| POST | `/v1/responses` | Cursor Agent Responses API shape |
| POST | `/v1/chat` | Native Lawful Nova receipt JSON |

Requests may use either `messages` (chat) or `input` (responses) — both normalize to the same governed path.

## Mission #002 / external verification

If you are an **external observer** validating integration hash and tunnel behavior, use the bundle at `nova-observer-bundle/` in project-infi — not this operator runbook. Observers use Cursor only; operators run Nova + tunnel on this guide.

## Related docs

- [README.md](README.md) — full shell install and stack ports
- [../docs/proof/NOVA_CURSOR_MISSION_002_DOSSIER.md](../docs/proof/NOVA_CURSOR_MISSION_002_DOSSIER.md) — proof dossier
- [../docs/contracts/NOVA_LSG_BOOTSTRAP.md](../docs/contracts/NOVA_LSG_BOOTSTRAP.md) — LSG bootstrap (full stack)
