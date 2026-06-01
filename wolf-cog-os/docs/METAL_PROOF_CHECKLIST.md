# Wolf CoG OS — Metal proof checklist (2.10+)

Run after flashing `Wolf-CoG-OS-full.iso` to USB and installing to internal disk.

## Install paths (pick one)

| Path | Steps |
|------|--------|
| **Live install** | Boot Live → desktop **Install Wolf CoG OS** → **Live install** → pick disk → reboot |
| **gtk d-i** | GRUB **Start Wolf CoG OS installer** → complete graphical install → reboot |
| **Terminal** | Boot Live → `sudo cogos-install apply --target /dev/sdX --yes --confirm-erase sdX` |

## gtk d-i WiFi (installer network)

1. **WiFi password** must be **8–64 characters** (WPA/WPA2 rule). Shorter/longer passwords show “Invalid passphrase”.
2. **Ethernet:** plug the cable in **before** the network step, then pick **`eth0` / `enp*`** (not `wlan*`).
3. If you backed out of WiFi to use Ethernet, wait up to **20s** for DHCP (3.2+ resets stale WiFi state automatically).
4. If still stuck: choose **Do not configure the network at this time** — install completes offline; fix network after first boot.
5. Debug (Ctrl+Alt+F2): `cat /var/log/cogos-di-wifi-probe.log` and `cat /var/log/cogos-di-netcfg-dispatch.log`

## First boot on internal disk

```bash
systemctl status cogos-firstboot.service cogos-governance.service cogos-spine.service cogos-observer.service accounts-daemon.service
journalctl -b -p err --no-pager | head -50
tail -50 /var/log/cogos-firstboot.log /var/log/cogos-governance.log
```

**Pass criteria**

- `cogos-firstboot.service`: exited 0 (oneshot)
- `accounts-daemon.service`: active
- `cogos-governance.service`: active (running)
- `cogos-spine.service` + `cogos-observer.service`: active

## Build-time proof (ISO builder)

- `$COGOS_WORK/proof/di-initrd-wifi/summary.txt` — initrd WiFi gate pass
- `$COGOS_WORK/proof/live-boot-integrity/validation.json` — live-safe gate pass
- `Wolf-CoG-OS-full.iso.sha256`

## Recovery (if daemons fail or boot loops)

Symptoms: `cogos-firstboot.service`, `cogos-governance.service`, `cogos-spine.service` failed at boot.

**Quick bypass (one boot):** GRUB → press `e` → add `cogos.safe=1` to the `linux` line → F10.

**Permanent fix from live USB** (root partition = `/dev/sdXN`):

```bash
sudo bash wolf-cog-os/scripts/fix-metal-boot-stack.sh /dev/sdXN
```

Also works for avahi/blueman boot-loop after install:

```bash
sudo bash wolf-cog-os/scripts/fix-boot-restart-loop.sh /dev/sdXN
```

Claim status: metal pass/fail is **proven** only after this checklist on target hardware.

## Nova narrative + intent rehydration (INV-1)

Pre-reboot on installed disk (companion turn or manual flush):

```bash
ls -la /opt/cogos/memory/operator/nova_narrative/ /opt/cogos/memory/operator/nova_intent/
# Expect operator.json and operator.intent.json after at least one cognitive companion turn
```

Reboot, then post-reboot:

```bash
export COGOS_RUNTIME=wolf
python3 -m src.cogos_runtime_bridge --rehydrate-boot operator \
  --narrative-store /opt/cogos/memory/operator/nova_narrative \
  --intent-store /opt/cogos/memory/operator/nova_intent
```

**Pass criteria**

- JSON output shows `"rehydrated": true` for both narrative and intent
- `active_story` matches pre-reboot snapshot
- `active_commitments` includes pre-reboot commitment IDs

Cross-machine proof bundle: `docs/proof/cognitive_runtime/INV1_WOLF_REHYDRATION_PROOF_BUNDLE.md`
