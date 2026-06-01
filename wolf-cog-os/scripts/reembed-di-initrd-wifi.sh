#!/usr/bin/env bash
# Re-embed d-i initrd WiFi stack on an existing COGOS_WORK tree (no full ISO rebuild).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export COGOS_WORK="${COGOS_UNIVERSAL_WORK:-${COGOS_WORK:-${HOME}/.cogos-universal-installer-work}}"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"
# shellcheck source=embed-cogos-in-di-initrd.sh
source "$SCRIPT_DIR/embed-cogos-in-di-initrd.sh"

WORK="$COGOS_WORK"

[[ -f "$WORK/iso/install/gtk/initrd.gz" ]] || {
  echo "ERROR: missing $WORK/iso/install/gtk/initrd.gz — run a full build first" >&2
  exit 1
}
[[ -f "$WORK/iso/install/wolf-cog-os/runtime.tar" ]] || {
  echo "ERROR: missing runtime.tar — run stage_di_iso_payload first" >&2
  exit 1
}

embed_cogos_in_di_initrd "$WORK/iso/install/wolf-cog-os/runtime.tar"
bash "$SCRIPT_DIR/verify-di-initrd-wifi.sh" "$WORK/iso/install/gtk/initrd.gz"
echo "d-i WiFi re-embed OK"
