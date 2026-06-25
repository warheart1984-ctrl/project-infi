# Mission #002 — Nova × Cursor × Nemotron Integration (Category B)

Status: **open** — implementation proof in progress; system proof not yet claimed.

**Full dossier:** [NOVA_CURSOR_MISSION_002_DOSSIER.md](./NOVA_CURSOR_MISSION_002_DOSSIER.md)  
**Observer bundle:** [nova-observer-bundle/](../../nova-observer-bundle/)

## Epistemic frame

| Layer | Question | Standard |
|-------|----------|----------|
| **Implementation proof** | Does the code path work when operated by the builder? | Internal checkpoints (replay, adapter, stream, tunnel) |
| **System proof** | Can someone else reproduce the same result without founder intervention? | Independent verification report |

> The proof is not the architecture. The proof is the independent reproduction.

Nova is **not** continuity-grade for Cursor until Category B succeeds.

---

## Integration path (must stay legible)

No hidden transforms. The intended path:

```
Cursor (cloud)
  → public HTTPS tunnel (ngrok or cloudflared)
  → Nova API /v1/chat/completions | /v1/responses
  → openai_cursor_compat (format detect + normalize only)
  → LawfulLLM.complete_openai()
  → HttpChatProvider
  → NVIDIA NIM (Nemotron-3-Ultra)
  → OpenAI-shaped response (+ X-Lawful-Nova-Receipt header)
```

Debuggability requires that each hop be observable (health, ngrok inspector, receipt header, provider errors surfaced).

---

## Implementation proof (internal)

These prove the **implementation**. They do **not** prove the **system**.

| # | Checkpoint | Pass criteria | Owner |
|---|------------|---------------|-------|
| I1 | Nemotron Ultra through Nova | `POST /v1/chat/completions` returns model text (not deterministic cortex stub); `/health` shows `frontier_configured: true` | Operator with valid `NVIDIA_API_KEY` |
| I2 | Tunnel without special handling | Cursor reaches Nova via public Base URL; requests visible in tunnel inspector | Operator with tunnel |
| I3 | Cursor Agent + Responses adapter | Agent payload with `input` (no `messages`) → 200; tool defs forwarded | Automated tests + Agent session |
| I4 | Streaming | `stream: true` → `text/event-stream` chunks | Automated tests + live probe |

**Current repo evidence for I3/I4:** `lawful-nova-shell/tests/test_local_nova_shell.py` (Responses format, models list, receipt header, tool normalization).

**I1/I2:** I1 pass on operator host (`frontier_configured: true`). I2 pending live Cursor session through public tunnel.

**Observer path:** external tester uses [nova-observer-bundle/](../../nova-observer-bundle/) only (Cursor client). Operator runs Nova + tunnel per dossier §12.

---

## System proof (Category B — external)

### Environment constraints (tester must satisfy)

- Fresh machine (or clean VM) — no pre-existing Nova/Cursor state assumed
- Fresh Cursor install with **Pro** (custom OpenAI base URL)
- Public tunnel active (tester’s own ngrok or cloudflared; reserved domain not required)
- Tester’s own **NVIDIA API key** from [build.nvidia.com](https://build.nvidia.com) (never use founder keys)
- No founder-side configuration, private env vars, or undocumented steps

### Reproduction steps (operator — runs Nova)

1. **Clone and bootstrap** (operator only)
   - Clone `project-infi`, create venv, `pip install -e ".[dev]"`
   - Copy `.env.example` → `.env`; set `NVIDIA_API_KEY`
   - Run LSG bootstrap per `docs/contracts/NOVA_LSG_BOOTSTRAP.md`

2. **Start Nova + tunnel**
   ```powershell
   .\scripts\start-nova-for-cursor.ps1 -FrontierProvider nvidia
   ```
   Or with explicit domain: `-NgrokDomain <your-subdomain>.ngrok-free.dev`

3. **Verify health (local)**
   - `GET http://127.0.0.1:8080/health` → `frontier_configured: true`, `frontier_provider: nvidia`

4. **Ask works**
   - Cursor Chat: simple prompt → Nemotron response through Nova (not cortex stub)

5. **Agent works**
   - Cursor Agent: prompt with tool use → no `missing messages` / Responses API errors

6. **Streaming works**
   - Partial output arrives incrementally when streaming is requested

7. **Tunnel works**
   - Cursor connects through public Base URL; requests appear in tunnel inspector (`http://127.0.0.1:4040` for ngrok)

8. **Adapter works**
   - No founder-side patches; stock `nova/openai_cursor_compat.py` path only

### Reproduction steps (external observer — Cursor only)

See **[NOVA_CURSOR_MISSION_002_DOSSIER.md](./NOVA_CURSOR_MISSION_002_DOSSIER.md)** §5 and [nova-observer-bundle/](../../nova-observer-bundle/).

Tester submits a **verification report** containing:

- Machine OS, Cursor version, date
- Tunnel type and public Base URL used (redact tokens)
- `/health` JSON snapshot
- One Ask transcript (prompt + response excerpt)
- One Agent transcript (including tool round if applicable)
- Tunnel inspector screenshot or request log excerpt
- Confirmation: no founder assistance, no manual hotfixes, no steps outside this doc + `lawful-nova-shell/README.md`

### Success condition

Independent tester reproduces the full integration path and submits the verification report. Only then may Mission #002 be marked **closed**.

---

## Cursor settings reference (tester copy)

| Setting | Value |
|---------|--------|
| Override OpenAI Base URL | `https://<your-tunnel-host>/v1` |
| API key | `local-nova` (placeholder; Nova does not validate) |
| Model | `lawful-nova` or `nvidia/nemotron-3-ultra-550b-a55b` |
| Network (if errors) | HTTP/1.1 |

---

## Known gaps before Category B can close

| Gap | Why it blocks system proof |
|-----|---------------------------|
| No completed external verification report | Category B undefined without it |
| `NVIDIA_API_KEY` is bring-your-own | Documented; not a founder secret |
| ngrok free interstitial / TLS quirks | Documented; tester may need HTTP/1.1 or cloudflared |
| Founder machine cannot TLS-probe own ngrok URL | Use inspector; documented in README |

---

## Related

- **Dossier:** [docs/proof/NOVA_CURSOR_MISSION_002_DOSSIER.md](../docs/proof/NOVA_CURSOR_MISSION_002_DOSSIER.md)
- **Observer bundle:** [nova-observer-bundle/](../nova-observer-bundle/)
- Operator setup: `lawful-nova-shell/README.md` (Lawful Nova / Cursor section)
- Env template: `.env.example` (`# --- Lawful Nova / Cursor ---`)
- Bootstrap: `scripts/start-nova-for-cursor.ps1`
- Automated contract tests: `lawful-nova-shell/tests/test_local_nova_shell.py`
