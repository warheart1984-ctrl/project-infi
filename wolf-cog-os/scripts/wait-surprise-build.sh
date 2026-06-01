#!/usr/bin/env bash
set -euo pipefail
SFS="${HOME}/.cogos-surprise-work-daily-driver-1.6-surprise/iso/live/filesystem.squashfs"
while pgrep -f 'mksquashfs.*surprise' >/dev/null 2>&1; do
  stat -c '%Y %s' "$SFS" 2>/dev/null || true
  sleep 60
done
echo "MKSQUASH_DONE $(stat -c '%y %s' "$SFS" 2>/dev/null || echo missing)"
while pgrep -f 'build.sh.*debian-live' >/dev/null 2>&1; do sleep 15; done
echo "BUILD_DONE"
ls -lh "${HOME}/Wolf-CoG-OS-daily-driver-surprise.iso" "${HOME}/Wolf-CoG-OS-daily-driver-surprise.iso.sha256" 2>/dev/null || true
cat "${HOME}/Wolf-CoG-OS-daily-driver-surprise.iso.sha256" 2>/dev/null || true
cp -f "${HOME}/Wolf-CoG-OS-daily-driver-surprise.iso" "${HOME}/Wolf-CoG-OS-daily-driver-surprise.iso.sha256" /mnt/e/project-infi/ 2>/dev/null || true
ls -lh /mnt/e/project-infi/Wolf-CoG-OS-daily-driver-surprise.iso* 2>/dev/null || true
