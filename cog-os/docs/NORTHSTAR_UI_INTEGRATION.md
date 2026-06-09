# NorthStar UI integration (daily-driver)

## Decision: Model B + kiosk autostart (Model A)

| Model | Choice | Notes |
|-------|--------|-------|
| **A — Kiosk browser** | **Yes (autostart)** | Chromium opens `/app/jarvis` after login |
| **B — Cinnamon + AAIS default** | **Yes (primary)** | LightDM autologin `cogos`, Cinnamon for settings/files |
| **C — Native Tauri/egui shell** | **Deferred** | Blueprint Phase 1; not in daily-driver v2 slice |

The forged **daily-driver** profile treats the packaged AAIS web shell (`/app`, Nova at `/nova`, Jarvis at `/jarvis`) as the operator surface. Cinnamon remains the session manager; the browser autostart provides a single-app feel without a new native client.

**Metal** and other forge profiles keep the AAIS **health stub only** on `:8765` — no operator UI staging required for forge proof.

## Runtime layout (daily-driver)

| Port | Service | Purpose |
|------|---------|---------|
| `8765` | `start-aais` health handler | Boot gate for `rc.sh`, `desktop.sh`, metal-compatible attestation |
| `8000` | `operator_ui_server.py` | Static React bundle at `/app/*`, `/health` for operator checks |

Static assets live under `/opt/cogos/app/static` (staged from monorepo `app/static` at forge build time).

## Session wiring

1. LightDM autologin: `cogos` → `cinnamon` (`/etc/lightdm/lightdm.conf.d/50-cogos-autologin.conf`)
2. XDG autostart: `chromium --app=http://127.0.0.1:8000/app/jarvis` (`~cogos/.config/autostart/cogos-operator.desktop`)
3. `desktop.sh` waits for operator UI HTTP 200 on `:8000/app/` before starting LightDM

## Proof

- Forge attestation gate: `operator_ui_http_200` (staged static + launcher + autostart)
- QEMU contract boot (daily-driver): hostfwd `:8000`, poll `/app/` HTTP 200
- See [BOOT_PROOF_CHECKLIST.md](./BOOT_PROOF_CHECKLIST.md) daily-driver section

## Non-goals (this slice)

OTA/WPR, native Tauri shell, full Cinnamon remaster, multi-user account polish, full `app/main.py` + Celery/Redis on image.
