# Nova Lawful Productization Status

This document records the current local productization boundary for the Lawful
Nova LLM slice.

## Local slice now wired

| Surface | Status | Verification |
| --- | --- | --- |
| Repo-local Python runtime | Ready | `lawful-nova-shell/setup/verify.ps1` (Windows) or `lawful-nova-shell/setup/verify.sh` (Linux/macOS) |
| Local Nova CLI | Ready | `lawful-nova-shell/bin/nova.ps1` (Windows) or `lawful-nova-shell/bin/nova` (Linux/macOS) |
| Local Nova API | Ready | `GET http://localhost:8080/health` |
| Direct LawfulLLM path | Ready | `scripts/nova_productization_gate.py` |
| Operator kernel + lawful brain | Ready when services are running | `GET /health` on ports `8790` and `8791` |

## Chain preservation contract

Every important Lawful Nova action signs a receipt that preserves four fields:

| Field | Purpose |
| --- | --- |
| `identity` | Records Nova instance, tier, operator session, and tenant. |
| `trace` | Records trace ID, ordered runtime stages, and ledger event name. |
| `authority_boundary` | Records that operator authority remains external and execution happens only after RSL acceptance. |
| `reproducibility` | Records prompt/output hashes, memory/tool-call hashes, and whether the deterministic core path was used. |

The local API exposes this as `chain` in `/v1/chat`, while the raw HMAC-signed
receipt keeps the same data under `receipt.payload`. The productization gate
checks this as `chain_contract`.

## Commands

**Windows (PowerShell):**

```powershell
. $env:USERPROFILE\.novarc.ps1
& $env:NOVA_CLI health --json
powershell -NoProfile -ExecutionPolicy Bypass -File E:\project-infi\scripts\start-nova-stack.ps1
powershell -ExecutionPolicy Bypass -File E:\project-infi\lawful-nova-shell\setup\verify.ps1
E:\project-infi\.venv\Scripts\python.exe scripts\nova_productization_gate.py
```

**Linux / macOS (bash — shared script for both):**

```bash
source /path/to/project-infi/lawful-nova-shell/setup/novrc.sh
./lawful-nova-shell/bin/nova health --json
./scripts/start-nova-stack.sh
./lawful-nova-shell/setup/verify.sh
./.venv/bin/python scripts/nova_productization_gate.py
```

## Current machine result

The Windows verifier reports all critical Lawful Nova checks passing:

- `NOVA_CLI` points at `E:\project-infi\lawful-nova-shell\bin\nova.ps1`.
- `NOVA_API_URL` responds at `http://localhost:8080`.
- `NOVA_VOSS_RUNTIME_PATH`, `NOVA_CORTEX_PATH`, and `NOVA_RSL_PATH` resolve to the local `nova/` runtime.
- Python resolves through the repo virtual environment.

Remaining warnings are external or optional for this local slice:

- `nvidia-smi` is not present, so GPU acceleration is unavailable.
- VS Code is not present.
- `fzf` is not present.

Docker is intentionally optional for the native Windows coding-agent path. Use
it later only for Linux parity, isolated CI, container deployment, or
GPU/container proof lanes.

## Remaining proof closure

These are not local code blockers, but they remain release evidence for a
hardware-backed or cross-machine production claim:

- Install or mount a vendor/hardware Voss/Cortex/RSL stack if the deployment
  target requires those assets outside the local `nova/` runtime.
- Add NVIDIA driver/CUDA/NIM evidence on a GPU machine.
- Run cross-machine Wolf reboot and continuity proof bundles.
- Complete operator rubric studies for continuity and coherence claims.
