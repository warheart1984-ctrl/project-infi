# Mission #002 Dossier — Nova Integration Reproduction

| Field | Value |
|-------|--------|
| **Mission ID** | 002 |
| **Mission type** | Founder-independent integration reproduction |
| **System under test** | Nova ↔ Nemotron Ultra ↔ Cursor |
| **Category target** | B (independent reproduction) |
| **Mechanism version** | 1.0 |
| **Observer** | TBD (external tester) |
| **Status** | OPEN |

---

## 1. Mission purpose

Demonstrate that the Nova ↔ Nemotron Ultra ↔ Cursor integration is:

- Reproducible
- Founder-independent
- Deterministic (integration hash)
- Legible (minimal path)
- Operational for an external Cursor observer

Mission #002 is the integration equivalent of Mission #001’s continuity proof (Bone King / `observer-bundle/`).

**The goal is not to show that Nova “works.”**  
**The goal is to show that someone else can make it work.**

---

## 2. Success criteria

The mission is **complete** when an external tester, on a fresh machine, can:

1. Install Cursor
2. Enable Nemotron Ultra (via the Nova endpoint behind the public tunnel)
3. Connect through the public tunnel
4. Send a request through Nova
5. Receive a Nemotron response
6. Use Cursor Agent through the Responses API adapter
7. Receive streaming output
8. Complete all steps **without founder assistance**
9. Submit a verification report with matching outputs and integration hash

When all nine conditions are met: **VERIFIED → COMPLETED**.

---

## 3. System architecture (minimal, legible path)

The integration path must remain:

```
Request → Adapter → Nova → Nemotron Ultra → Response
```

Expanded hop map:

| Hop | Component | Role |
|-----|-----------|------|
| Client | Cursor (cloud) | Sends Chat Completions or Responses API payloads |
| Ingress | Public HTTPS tunnel (ngrok / cloudflared) | Cursor cloud → operator-hosted Nova |
| API | `nova/api` — `/v1/chat/completions`, `/v1/responses` | OpenAI-compatible surface |
| Adapter | `nova/openai_cursor_compat.py` | Detect format; normalize `input` → `messages`; normalize tools only |
| Runtime | `LawfulLLM.complete_openai()` | Governed completion path |
| Frontier | `HttpChatProvider` → NVIDIA NIM | `nvidia/nemotron-3-ultra-550b-a55b` |
| Egress | OpenAI-shaped JSON + `X-Lawful-Nova-Receipt` | Cursor-compatible response; governance in header |

No hidden transforms. No silent rewrites. No founder-only configuration in the observer bundle.

---

## 4. Roles

| Role | Responsibility | Needs repo clone? |
|------|----------------|-------------------|
| **Mission operator** | Runs Nova + Nemotron + tunnel; holds `NVIDIA_API_KEY`; sets `tunnel_url.txt`; regenerates expected hash; dispatches bundle | Yes (`project-infi`) |
| **External observer** | Fresh Cursor; runs three tests; computes hash; submits report | No — `nova-observer-bundle/` only |
| **Founder** | Must not be required during observer reproduction | — |

---

## 5. Observer instructions

Primary doc: **[nova-observer-bundle/README.md](../../nova-observer-bundle/README.md)**

Short pointer: **[nova-observer-bundle/verification/instructions.md](../../nova-observer-bundle/verification/instructions.md)**

### Environment requirements (observer)

- Fresh machine (no prior Nova or Cursor integration config)
- Fresh Cursor install (**Pro+** — custom OpenAI base URL)
- Public tunnel URL in `tunnel_url.txt` (set by mission operator before dispatch)
- Python 3.10+ (for `tools/integration_hash.py` only)
- Internet connection
- **No founder assistance**

### Observer steps (summary)

| Step | Action |
|------|--------|
| 1 | Install Cursor; initialize defaults |
| 2 | Copy URL from `tunnel_url.txt` → Cursor **Override OpenAI Base URL** (`…/v1`) |
| 3 | API key: `local-nova`; model: `lawful-nova` or `nvidia/nemotron-3-ultra-550b-a55b` |
| 4 | **Basic request** — prompt in `expected_outputs/basic_request.md` |
| 5 | **Agent** — task in `expected_outputs/agent_request.md` |
| 6 | **Streaming** — prompt in `expected_outputs/streaming_request.md` |
| 7 | Run `python tools/integration_hash.py`; compare to `expected_integration_hash.txt` |
| 8 | Complete `verification/report_template.md` → `verification/report_<name>.md` |

### Cursor settings (observer copy)

| Setting | Value |
|---------|--------|
| Override OpenAI Base URL | From `tunnel_url.txt` (e.g. `https://<host>.ngrok-free.dev/v1`) |
| API key | `local-nova` |
| Model | `lawful-nova` or `nvidia/nemotron-3-ultra-550b-a55b` |
| Network (if errors) | HTTP/1.1 |

---

## 6. Expected outputs (canonical forms)

Structural expectations — not literal strings.

| Test | Prompt / task | Spec |
|------|---------------|------|
| Basic | `Hello Nova. Please confirm you are routing to Nemotron Ultra.` | [basic_request.md](../../nova-observer-bundle/expected_outputs/basic_request.md) |
| Agent | `Create a file named test.txt with the text "Nova integration test successful."` | [agent_request.md](../../nova-observer-bundle/expected_outputs/agent_request.md) |
| Streaming | `Stream a 5-sentence response, one sentence at a time.` | [streaming_request.md](../../nova-observer-bundle/expected_outputs/streaming_request.md) |

### Structural pass criteria (all tests)

- No `missing messages` / 422 from Responses-vs-Chat mismatch
- No deterministic cortex stub when frontier is live (`Under RSL, Nova Cortex reads…` only when `frontier_configured: false`)
- No founder-specific paths or undocumented env in responses
- Agent: tool invocation + `test.txt` with exact content
- Streaming: multiple SSE chunks, not one buffered blob

---

## 7. Integration hash (canonical equivalent)

Mission #001 used a canonical package hash (`observer-bundle/BK-PKG-1.json`). Mission #002 uses an **integration hash** — SHA-256 over sorted JSON metadata.

### Hash inputs

| Field | Source |
|-------|--------|
| `tunnel_url` | `tunnel_url.txt` (must match mission dispatch) |
| `cursor_version` | `CURSOR_VERSION` env or `"unknown"` |
| `nova_version` | `NOVA_VERSION` env or `"unknown"` |
| `nemotron_model` | `NEMOTRON_MODEL` env or `"Nemotron Ultra"` |
| `adapter_version` | `NOVA_ADAPTER_VERSION` env or `"1.0"` |
| `protocol_version` | `"1.0"` |

**Algorithm:** `SHA256(json.dumps(metadata, sort_keys=True))`

### Tool

```bash
cd nova-observer-bundle
python tools/integration_hash.py
```

Writes `integration_hash_observed.txt` and prints metadata + digest.

### Reference artifact

`expected_integration_hash.txt` — coordinator regenerates when tunnel is published:

```bash
python tools/integration_hash.py \
  --tunnel-url https://<subdomain>.ngrok-free.dev/v1 \
  --write-expected
```

**Reference tunnel (pre-dispatch placeholder):** `https://mission-002-reference.example/v1`  
**Reference SHA256:** `3c9ed20c5217b9550d447021bdac6cca4b73e7890a265d976fb6d823f54c86e1`

Observer hash must match the coordinator-published `expected_integration_hash.txt` for the dispatched `tunnel_url.txt`.

---

## 8. External tester bundle

**Path:** [nova-observer-bundle/](../../nova-observer-bundle/)

```text
nova-observer-bundle/
├── README.md
├── tunnel_url.txt
├── expected_integration_hash.txt
├── expected_outputs/
│   ├── basic_request.md
│   ├── agent_request.md
│   └── streaming_request.md
├── verification/
│   ├── report_template.md
│   └── instructions.md
└── tools/
    └── integration_hash.py
```

| Requirement | Status |
|-------------|--------|
| No founder-only secrets | ✓ |
| No private API keys | ✓ |
| No required observer env vars | ✓ (optional version overrides only) |
| No hidden dependencies | ✓ (stdlib + Cursor) |
| Pure Python + text files | ✓ |

Analogue: Mission #001 [observer-bundle/](../../observer-bundle/) (Bone King continuity proof).

---

## 9. Verification template

**Path:** [nova-observer-bundle/verification/report_template.md](../../nova-observer-bundle/verification/report_template.md)

Observer fills: environment, three test results (PASS/FAIL), integration hash match, founder-assistance declaration, final verdict **VERIFIED** or **FAILED**.

---

## 10. Completion condition

Mission #002 → **COMPLETED** when:

- External tester completes all observer steps
- Expected structural outputs match `expected_outputs/`
- Integration hash matches `expected_integration_hash.txt`
- No founder assistance required
- Verification report submitted with verdict **VERIFIED**

This is the Nova equivalent of Bradley’s Mission #001 reproduction.

### State machine

```text
OPEN          → implementation in progress; no external report
VERIFIED      → external report submitted; all tests PASS; hash match
COMPLETED     → coordinator accepts report; mission closed
FAILED        → report documents blockers; mission may reopen after fixes
```

---

## 11. Implementation vs system proof

| Layer | Question | Evidence |
|-------|----------|----------|
| **Implementation proof** | Does the code path work when operated by the builder? | Automated tests; operator `/health` |
| **System proof** | Can someone else reproduce without founder help? | External verification report + hash match |

> The proof is not the architecture. The proof is the independent reproduction.

### Implementation proof checklist (internal)

| ID | Checkpoint | Pass criteria | Status |
|----|------------|---------------|--------|
| I1 | Nemotron through Nova | `/health` → `frontier_configured: true`; real model text | **Pass** (operator env) |
| I2 | Tunnel | Cursor reaches public URL; requests in ngrok inspector | Pending live Cursor test |
| I3 | Agent + Responses adapter | `input`-only payload → 200; tools forwarded | **Pass** (automated tests) |
| I4 | Streaming | `stream: true` → SSE chunks | **Pass** (automated + live probe) |

**Automated evidence:** `lawful-nova-shell/tests/test_local_nova_shell.py`, `tests/test_nova_mission_002_hash.py`

**System proof:** **Not claimed** — no external verification report yet.

---

## 12. Operator runbook (not observer-facing)

### 12.1 Prerequisites

- `project-infi` cloned; `pip install -e ".[dev]"`
- `.env` from `.env.example`; `NVIDIA_API_KEY` set (never commit)
- `NOVA_FRONTIER_PROVIDER=nvidia`
- LSG bootstrap: `docs/contracts/NOVA_LSG_BOOTSTRAP.md`

### 12.2 Start Nova + tunnel

```powershell
cd E:\project-infi
.\scripts\start-nova-for-cursor.ps1 `
  -FrontierProvider nvidia `
  -NgrokDomain scoreless-calzone-plant.ngrok-free.dev
```

Verify locally:

```text
GET http://127.0.0.1:8080/health
→ frontier_configured: true
→ frontier_provider: nvidia
```

Do **not** rely on TLS-probing the public ngrok URL from the operator PC if local TLS fails; use ngrok inspector at `http://127.0.0.1:4040`.

### 12.3 Publish observer bundle

```powershell
cd E:\project-infi\nova-observer-bundle

# 1. Set tunnel_url.txt to public Base URL, e.g.:
#    https://scoreless-calzone-plant.ngrok-free.dev/v1

# 2. Regenerate expected hash
python tools/integration_hash.py `
  --tunnel-url https://scoreless-calzone-plant.ngrok-free.dev/v1 `
  --write-expected

# 3. Dispatch nova-observer-bundle/ to external observer (zip or share)
```

Optional coordinator env when regenerating hash for audit trail:

```powershell
$env:NOVA_VERSION = "0.1.0"
$env:NEMOTRON_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"
```

Share `NOVA_VERSION` with observer if they should set `NOVA_VERSION` before running the hash tool.

### 12.4 Accept verification report

Coordinator checks:

- All three tests PASS
- Hash match
- Founder assistance = NO
- Final verdict = VERIFIED

Then update this dossier **Status** to **COMPLETED**.

---

## 13. Known gaps (before Category B closes)

| Gap | Mitigation |
|-----|------------|
| No external verification report | Dispatch bundle; await `report_<name>.md` |
| ngrok free interstitial / TLS quirks | HTTP/1.1 in Cursor; or `-Tunnel cloudflared` |
| Operator PC cannot TLS-probe own ngrok URL | Use ngrok inspector |
| NVIDIA key is operator-only | Never in observer bundle; observer never needs it |

---

## 14. Related artifacts

| Artifact | Path |
|----------|------|
| Summary / epistemic frame | [NOVA_CURSOR_MISSION_002.md](./NOVA_CURSOR_MISSION_002.md) |
| Observer bundle | [nova-observer-bundle/](../../nova-observer-bundle/) |
| Operator README | [lawful-nova-shell/README.md](../../lawful-nova-shell/README.md) |
| Env template | [.env.example](../../.env.example) |
| Bootstrap script | [scripts/start-nova-for-cursor.ps1](../../scripts/start-nova-for-cursor.ps1) |
| API tests | [lawful-nova-shell/tests/test_local_nova_shell.py](../../lawful-nova-shell/tests/test_local_nova_shell.py) |
| Hash tests | [tests/test_nova_mission_002_hash.py](../../tests/test_nova_mission_002_hash.py) |
| Mission #001 analogue | [observer-bundle/](../../observer-bundle/) |
