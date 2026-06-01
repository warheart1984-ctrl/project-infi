#!/usr/bin/env bash
# Post-embed gate: gtk d-i initrd must contain WiFi stack + probe + preseed flags.
set -euo pipefail

WORK="${COGOS_WORK:?}"
INITRD="${1:-$WORK/iso/install/gtk/initrd.gz}"
PROOF_DIR="${COGOS_DI_WIFI_PROOF_DIR:-$WORK/proof/di-initrd-wifi}"
TMP="$PROOF_DIR/extract"

[[ -f "$INITRD" ]] || {
  echo "ERROR: verify-di-initrd-wifi: missing $INITRD" >&2
  exit 1
}

mkdir -p "$PROOF_DIR"
rm -rf "$TMP"
mkdir -p "$TMP"

gzip -dc "$INITRD" | (cd "$TMP" && cpio -idm --quiet 2>/dev/null || cpio -idm --quiet)

fail=0
check() {
  if eval "$2"; then
    echo "OK  $1"
  else
    echo "FAIL $1"
    fail=1
  fi
}

check "preseed load_firmware" "grep -q 'hw-detect/load_firmware boolean true' '$TMP/preseed.cfg'"
check "preseed nonfree firmware" "grep -q 'hw-detect/install-with-nonfree boolean true' '$TMP/preseed.cfg'"
check "preseed wifi early_command" "grep -q 'cogos-di-wifi-probe.sh' '$TMP/preseed.cfg'"
check "preseed netcfg dispatch" "grep -q 'cogos-di-netcfg-dispatch.sh' '$TMP/preseed.cfg'"
check "preseed link_wait_timeout" "grep -q 'netcfg/link_wait_timeout' '$TMP/preseed.cfg'"
check "preseed dhcp_timeout" "grep -q 'netcfg/dhcp_timeout' '$TMP/preseed.cfg'"
check "no invalid dhcp_options note" "! grep -q '^d-i netcfg/dhcp_options note' '$TMP/preseed.cfg'"
check "wifi probe in start.d" "test -x '$TMP/lib/debian-installer/start.d/zz-cogos-wifi'"
check "cfg80211 module present" "find '$TMP/lib/modules' '$TMP/usr/lib/modules' -name 'cfg80211.ko*' 2>/dev/null | grep -q ."
check "wireless driver present (rtw88 or iwlwifi)" \
  "{ find '$TMP/lib/modules' '$TMP/usr/lib/modules' -name 'rtw88_8822bu.ko*' 2>/dev/null | grep -q . || \
     find '$TMP/lib/modules' '$TMP/usr/lib/modules' -path '*iwlwifi/iwlwifi.ko*' 2>/dev/null | grep -q .; }"
check "modules.alias wireless" "grep -rqE 'iwlwifi|rtw88|brcmfmac' '$TMP/lib/modules' '$TMP/usr/lib/modules' 2>/dev/null"

if (( fail )); then
  echo "ERROR: d-i initrd WiFi verification failed" >&2
  exit 1
fi

cat > "$PROOF_DIR/summary.txt" <<EOF
initrd=$INITRD
verified=$(date -u +%Y-%m-%dT%H:%M:%SZ)
status=pass
EOF
echo "d-i initrd WiFi verification passed: $INITRD"
