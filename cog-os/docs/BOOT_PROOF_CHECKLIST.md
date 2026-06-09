# Boot proof checklist (all profiles)

Generic boot verification for **cog-os** — custom init spine, service table, and profile-specific desktop or console login.

## Quick reference

| Profile | PID 1 | Desktop / login | Primary proof command |
|---------|--------|-----------------|------------------------|
| `metal` | Custom `init` → `rc.sh` | `login` (agetty autologin) | `make cog-qemu-smoke-contract-boot COG_PROFILE=metal` |
| `daily-driver` | Hybrid init + systemd units | LightDM / Cinnamon + operator UI kiosk | `make cog-qemu-smoke-contract-boot COG_PROFILE=daily-driver` |
| `forge-selfhosted` | Same as daily-driver + UL hooks | LightDM + optional UL smoke | Forge CI / self-hosted workflow |

## 1. Init and service table

- [ ] `/sbin/init` is CoG build from `cog-os/host/src/init.c`
- [ ] `/etc/init.conf` matches forge profile (`cog-os/forge/profiles/<profile>.yaml`)
- [ ] `/etc/rc.sh` runs only services allowed for profile (`desktop` on daily-driver; `login` on metal)
- [ ] Logs under `/var/log/cog/init.log` show service start order without fatal errors

## 2. Platform / network

- [ ] `platform` service completes (`/run/cog/platform.done` or log line)
- [ ] In QEMU slirp: guest has routable address on primary NIC (`10.0.2.15/24` typical)
- [ ] Loopback up; DNS/resolver optional for metal proof

## 3. AAIS health gate

- [ ] `aais` service starts `start-aais`
- [ ] `/run/cog/aais.health` present
- [ ] `curl -sf http://127.0.0.1:8765/health` returns JSON with `"status":"ok"`

## 4. Profile-specific login

### Metal

- [ ] `login` service runs (see [METAL_PROOF_CHECKLIST.md](./METAL_PROOF_CHECKLIST.md))
- [ ] Console autologin as `cogos` on tty1

### Daily-driver

- [ ] `desktop` service starts LightDM (or documented fallback)
- [ ] Operator UI staged: `/opt/cogos/app/static/index.html`, `/opt/cogos/lib/operator_ui_server.py`
- [ ] `start-aais` serves health on `:8765` and operator UI on `:8000` when `COG_PROFILE=daily-driver`
- [ ] `curl -sf http://127.0.0.1:8000/app/` returns HTTP 200 (SPA shell)
- [ ] LightDM autologin `cogos` → Cinnamon (`/etc/lightdm/lightdm.conf.d/50-cogos-autologin.conf`)
- [ ] Chromium autostart opens `/app/jarvis` (`~cogos/.config/autostart/cogos-operator.desktop`)
- [ ] Forge attestation gate `operator_ui_http_200` passes on built rootfs
- [ ] Graphical session reachable after boot (manual check on hardware if needed)

## 5. First boot

- [ ] `/opt/cogos/memory/operator/FIRST_BOOT_PENDING` consumed or handled by `firstboot` service
- [ ] No blocking errors in firstboot log

## 6. CI contract

Required for merge / promotion when touching boot path:

```bash
make cog-qemu-smoke-contract-boot COG_PROFILE=metal
make cog-qemu-smoke-contract-boot COG_PROFILE=daily-driver
make installer-integration
```

Metal contract asserts serial boot + AAIS `/health` on `:8765`. Daily-driver adds operator UI `/app/` HTTP 200 on `:8000`.

## 7. Failure triage

| Symptom | Likely cause | Check |
|---------|--------------|--------|
| AAIS health timeout from host | Guest not on slirp IP; port not forwarded | `platform.sh`, `qemu-smoke.sh` hostfwd |
| `validate-config` fails | Payload not staged | `forge/scripts/lib/payload-stage.sh`, `/opt/cogos/lib/src` |
| No getty on metal | `login` missing from profile or `agetty` not in rootfs | `metal.yaml`, `packages/base.txt` |
| LightDM missing | `desktop` skipped or profile not daily-driver | `rc.sh` `should_run_service`, profile packages |
| Operator UI 404 / timeout | Static bundle not staged or wrong profile in `start-aais` | `payload-stage.sh`, `app/static`, `/etc/cog/profile` |
| Chromium autostart missing | Session install skipped | `install-daily-driver-session.sh`, cogos home autostart |

## Related docs

- [METAL_PROOF_CHECKLIST.md](./METAL_PROOF_CHECKLIST.md) — metal-specific forge proof
- [NORTHSTAR_UI_INTEGRATION.md](./NORTHSTAR_UI_INTEGRATION.md) — daily-driver operator UI model
- [../forge/README.md](../forge/README.md) — build entrypoints (if present)
- Monorepo `Makefile` — `cog-rootfs`, `cog-qemu-smoke-contract-boot`, `forge-installer`
