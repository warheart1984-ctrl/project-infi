#!/usr/bin/env bash
# Normalize CoGOS boot stack scripts to LF (Windows checkout safe for metal PID1).
set -euo pipefail

normalize_boot_stack_lf() {
  local root="${1:?rootfs or mount path}"
  local fix_py dir f count=0

  fix_py="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/fix-sh-lf.py"
  [[ -f "$fix_py" ]] || {
    echo "ERROR: normalize_boot_stack_lf: missing $fix_py" >&2
    return 1
  }

  for dir in \
    "$root/usr/lib/cogos" \
    "$root/usr/local/bin" \
    "$root/etc/systemd/system"; do
    [[ -d "$dir" ]] || continue
    while IFS= read -r -d '' f; do
      case "$f" in
        *.sh|*.service|*.conf|*/cogos-*|*/firstboot.sh|*/governance*|*/spine|*/observer|*/boot-service-hardening.sh)
          python3 "$fix_py" "$f"
          count=$((count + 1))
          ;;
      esac
    done < <(find "$dir" -maxdepth 3 -type f -print0 2>/dev/null)
  done

  echo "[boot-stack-lf] normalized $count launcher(s) under $root"
}

verify_boot_stack_lf() {
  local root="${1:?}"
  local bad=0 f
  while IFS= read -r -d '' f; do
    if grep -q $'\r' "$f" 2>/dev/null; then
      echo "FAIL CRLF: $f" >&2
      bad=1
    fi
  done < <(find "$root/usr/lib/cogos" "$root/etc/systemd/system" -maxdepth 3 -type f -print0 2>/dev/null)
  return "$bad"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  normalize_boot_stack_lf "${1:?root path}"
  verify_boot_stack_lf "$1"
fi
