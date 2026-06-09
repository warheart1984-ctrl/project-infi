#!/bin/bash
set -euo pipefail
RUN=/run/cog
mkdir -p "$RUN" /var/log/cog
# Loopback and virtio NIC must be up before AAIS / hostfwd health checks.
ip link set lo up 2>/dev/null || true
for attempt in $(seq 1 30); do
  if ls /sys/class/net/ens3 /sys/class/net/eth0 /sys/class/net/enp0s1 2>/dev/null | grep -q .; then
    break
  fi
  sleep 1
done
for dev in eth0 enp0s1 enp0s3 ens3; do
  ip link set "$dev" up 2>/dev/null || true
done
# Bring up any remaining interfaces (predictable names vary by kernel/QEMU).
for dev_path in /sys/class/net/*; do
  dev="$(basename "$dev_path")"
  [[ "$dev" == "lo" ]] && continue
  ip link set "$dev" up 2>/dev/null || true
done
# QEMU user/slirp networking: assign default guest address when no DHCP client is present.
SLIRP_DEV=""
for cand in ens3 eth0 enp0s1; do
  if [[ -d "/sys/class/net/$cand" ]]; then
    SLIRP_DEV="$cand"
    break
  fi
done
if [[ -n "$SLIRP_DEV" ]]; then
  ip addr add 10.0.2.15/24 dev "$SLIRP_DEV" 2>/dev/null || true
  ip route add default via 10.0.2.2 dev "$SLIRP_DEV" 2>/dev/null || true
fi
if command -v dhclient >/dev/null 2>&1; then
  for dev in ens3 eth0 enp0s1; do
    dhclient -1 -q "$dev" 2>/dev/null && break
  done
elif command -v udhcpc >/dev/null 2>&1; then
  for dev in ens3 eth0 enp0s1; do
    udhcpc -i "$dev" -q -n 2>/dev/null && break
  done
fi
date -Iseconds >"$RUN/platform.ready"
echo "platform heartbeat at $(date -Iseconds)" >>/var/log/cog/init.log
