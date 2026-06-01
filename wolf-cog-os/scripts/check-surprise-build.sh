#!/usr/bin/env bash
ps aux | grep surprise | grep -v grep || true
ps aux | grep build.sh | grep -v grep || true
ps aux | grep mksquash | grep -v grep || true
stat -c '%y %s' "${HOME}/.cogos-surprise-work/iso/live/filesystem.squashfs" 2>/dev/null || true
ls -lh "${HOME}/Wolf-CoG-OS-daily-driver-surprise.iso" 2>/dev/null || true
