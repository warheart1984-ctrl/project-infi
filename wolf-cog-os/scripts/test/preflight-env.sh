#!/usr/bin/env bash
set -euo pipefail

SCRIPT_NAME="$(basename "$0")"

usage() {
  cat <<'EOF'
Usage:
  preflight-env.sh [--privileged] [--iso PATH] [--rootfs PATH]

Options:
  --privileged   Require non-interactive sudo readiness (for rootfs/apply stages).
  --iso PATH     Validate that ISO path exists and is readable.
  --rootfs PATH  Validate that rootfs tree path exists (tree-mode preflight).
  -h, --help     Show this help.
EOF
}

log_ok()   { printf '[preflight][ok] %s\n' "$*"; }
log_warn() { printf '[preflight][warn] %s\n' "$*"; }
log_err()  { printf '[preflight][error] %s\n' "$*" >&2; }

need_tools=(
  bash
  python3
  rsync
  unsquashfs
  mksquashfs
  xorriso
  qemu-img
  qemu-system-x86_64
  wget
  unzip
)

require_privileged=0
iso_path=""
rootfs_path=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --privileged)
      require_privileged=1
      shift
      ;;
    --iso)
      iso_path="${2:-}"
      [[ -n "$iso_path" ]] || { log_err "--iso requires a value"; usage; exit 2; }
      shift 2
      ;;
    --rootfs)
      rootfs_path="${2:-}"
      [[ -n "$rootfs_path" ]] || { log_err "--rootfs requires a value"; usage; exit 2; }
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      log_err "Unknown argument: $1"
      usage
      exit 2
      ;;
  esac
done

fails=0
warns=0

for tool in "${need_tools[@]}"; do
  if command -v "$tool" >/dev/null 2>&1; then
    log_ok "tool available: $tool"
  else
    log_err "missing required tool: $tool"
    fails=$((fails + 1))
  fi
done

tmp_avail_kb="$(df -Pk /tmp | awk 'NR==2 {print $4}')"
tmp_avail_gb="$((tmp_avail_kb / 1024 / 1024))"
if (( tmp_avail_gb < 6 )); then
  log_warn "/tmp has ${tmp_avail_gb}GiB free (<6GiB). Large ISO downloads may fail. Use a larger path."
  warns=$((warns + 1))
else
  log_ok "/tmp free space: ${tmp_avail_gb}GiB"
fi

if [[ -n "$iso_path" ]]; then
  if [[ -f "$iso_path" && -r "$iso_path" ]]; then
    log_ok "ISO path is readable: $iso_path"
  else
    log_err "ISO path not found/readable: $iso_path"
    fails=$((fails + 1))
  fi
fi

if [[ -n "$rootfs_path" ]]; then
  if [[ -d "$rootfs_path" ]]; then
    log_ok "rootfs path exists: $rootfs_path"
  else
    log_err "rootfs path not found: $rootfs_path"
    fails=$((fails + 1))
  fi
fi

if (( require_privileged == 1 )); then
  if ! command -v sudo >/dev/null 2>&1; then
    log_err "sudo is required for privileged preflight"
    fails=$((fails + 1))
  elif sudo -n true >/dev/null 2>&1; then
    log_ok "sudo non-interactive check passed"
  else
    log_err "sudo non-interactive check failed (password prompt or policy required)"
    fails=$((fails + 1))
  fi
fi

printf '[preflight] summary: errors=%d warnings=%d\n' "$fails" "$warns"
if (( fails > 0 )); then
  exit 1
fi
