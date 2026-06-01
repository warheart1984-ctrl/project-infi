#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ISO_PATH="${ISO:-$ROOT_DIR/wolf-cog-os/output/wolf-cog-os-${COGOS_TAG:-12.22.0-wolf-os}.iso}"
WORK_DIR="${COGOS_QEMU_WORK:-/tmp/cogos-qemu-smoke}"
SERIAL_LOG="$WORK_DIR/serial.log"
WAIT_SECS="${COGOS_QEMU_WAIT:-90}"
PID=""

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing command: $1" >&2; exit 2; }
}

cleanup() {
  if [[ -n "$PID" ]] && kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    sleep 2
    kill -9 "$PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

require qemu-system-x86_64

if [[ ! -f "$ISO_PATH" ]]; then
  echo "ISO not found for QEMU smoke test: $ISO_PATH" >&2
  exit 3
fi

mkdir -p "$WORK_DIR"
rm -f "$SERIAL_LOG"

qemu-system-x86_64 \
  -m 4096 \
  -cdrom "$ISO_PATH" \
  -boot d \
  -nographic \
  -serial "file:$SERIAL_LOG" \
  -no-reboot >/dev/null 2>&1 &
PID="$!"

sleep "$WAIT_SECS"

if ! kill -0 "$PID" 2>/dev/null; then
  echo "QEMU exited early. Serial output:" >&2
  [[ -f "$SERIAL_LOG" ]] && tail -n 80 "$SERIAL_LOG" >&2 || true
  exit 4
fi

echo "QEMU smoke boot stayed alive for $WAIT_SECS seconds."
