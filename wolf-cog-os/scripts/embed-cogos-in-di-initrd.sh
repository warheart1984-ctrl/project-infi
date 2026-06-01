#!/usr/bin/env bash
# Embed CoGOS payload + preseed + late hook into Debian gtk/text installer initrd images.
set -euo pipefail

_rootfs_kver() {
  local rootfs="${WORK:?}/rootfs"
  local kver
  kver="$(find "$rootfs/lib/modules" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null | sort | head -n 1)"
  [[ -n "$kver" ]] || {
    echo "ERROR: no kernel modules under $rootfs/lib/modules" >&2
    return 1
  }
  printf '%s' "$kver"
}

_di_install_kver() {
  local vmlinuz="${WORK:?}/iso/install/gtk/vmlinuz"
  local kver=""
  [[ -f "$vmlinuz" ]] || vmlinuz="${WORK}/iso/install/vmlinuz"
  [[ -f "$vmlinuz" ]] || {
    echo "ERROR: no install vmlinuz under $WORK/iso/install/" >&2
    return 1
  }
  if command -v strings >/dev/null 2>&1; then
    kver="$(strings "$vmlinuz" 2>/dev/null | grep -m1 '^Linux version ' \
      | sed -n 's/Linux version \([0-9][^ ]*\).*/\1/p')"
  fi
  if [[ -z "$kver" ]]; then
    kver="$(_rootfs_kver)"
    echo "[4e/9] WARN: could not parse install vmlinuz kver — using rootfs $kver" >&2
  fi
  printf '%s' "$kver"
}

_assert_di_kver_match() {
  local rootfs_kver di_kver
  rootfs_kver="$(_rootfs_kver)"
  di_kver="$(_di_install_kver)"
  if [[ "$rootfs_kver" != "$di_kver" ]]; then
    echo "ERROR: kernel mismatch: live rootfs=$rootfs_kver install vmlinuz=$di_kver" >&2
    echo "ERROR: WiFi module inject would vermagic-fail — rebuild with matched substrate" >&2
    return 1
  fi
  echo "[4e/9] install vmlinuz kver matches live rootfs ($di_kver)"
}

_initrd_modules_dir() {
  local root="$1"
  local kver="$2"
  if [[ -e "$root/lib/modules/$kver" ]]; then
    printf '%s/lib/modules/%s' "$root" "$kver"
    return 0
  fi
  if [[ -d "$root/usr/lib/modules/$kver" ]]; then
    printf '%s/usr/lib/modules/%s' "$root" "$kver"
    return 0
  fi
  return 1
}

_initrd_firmware_dir() {
  local root="$1"
  if [[ -e "$root/lib/firmware" ]]; then
    printf '%s/lib/firmware' "$root"
    return 0
  fi
  if [[ -d "$root/usr/lib/firmware" ]]; then
    printf '%s/usr/lib/firmware' "$root"
    return 0
  fi
  printf '%s/lib/firmware' "$root"
}

_merge_wifi_overlay_into_initrd() {
  local root="$1"
  local extra_dir="$2"
  local kver="$3"
  local mod_dst fw_dst

  mod_dst="$(_initrd_modules_dir "$root" "$kver")" || {
    echo "[4e/9] WARN: initrd has no modules tree for $kver" >&2
    return 0
  }
  if [[ -d "$extra_dir/usr/lib/modules/$kver" ]]; then
    mkdir -p "$mod_dst"
    cp -a "$extra_dir/usr/lib/modules/$kver/." "$mod_dst/"
    echo "[4e/9] merged WiFi modules into $(basename "$(dirname "$mod_dst")")/$(basename "$mod_dst")"
  fi

  fw_dst="$(_initrd_firmware_dir "$root")"
  if [[ -d "$extra_dir/usr/lib/firmware" ]]; then
    mkdir -p "$fw_dst"
    cp -a "$extra_dir/usr/lib/firmware/." "$fw_dst/"
    echo "[4e/9] merged WiFi firmware into $(basename "$(dirname "$fw_dst")")/$(basename "$fw_dst")"
  fi
}

# Copy WiFi firmware from merged live rootfs into d-i initrd overlay.
_stage_di_initrd_wifi_firmware() {
  local extra_root="${1:?}"
  local rootfs="${WORK:?}/rootfs"
  local fw_src="$rootfs/lib/firmware"
  local fw_dst="$extra_root/usr/lib/firmware"
  local dir copied=0

  [[ -d "$fw_src" ]] || {
    echo "[4e/9] WARN: no $fw_src — skipping WiFi firmware inject into d-i initrd" >&2
    return 0
  }

  mkdir -p "$fw_dst"
  for dir in rtw89 rtw88 rtl_bt rtlwifi rtl8733 rtl8761 rtl8821 rtl8852 \
    ath10k ath11k ath12k brcm mediatek; do
    [[ -d "$fw_src/$dir" ]] || continue
    cp -a "$fw_src/$dir" "$fw_dst/"
    copied=1
  done
  while IFS= read -r -d '' blob; do
    cp -a "$blob" "$fw_dst/"
    copied=1
  done < <(find "$fw_src" -maxdepth 1 \( \
    -name 'rtl_*' -o -name 'RTW*' -o -name 'rtw*' \
    -o -name 'iwlwifi-*' -o -name 'iwlwifi-*.ucode' \
    \) -print0 2>/dev/null)
  if [[ -d "$fw_src/iwlwifi" ]]; then
    cp -a "$fw_src/iwlwifi" "$fw_dst/"
    copied=1
  fi

  if (( copied )); then
    echo "[4e/9] Staged WiFi firmware for d-i initrd ($(du -sh "$fw_dst" | awk '{print $1}'))"
  else
    echo "[4e/9] WARN: no WiFi firmware found under $fw_src" >&2
  fi
}

# Stock gtk/text d-i initrd ships ~800 modules but no rtw88/cfg80211 stack; inject from live rootfs.
_stage_di_initrd_wifi_modules() {
  local extra_root="${1:?}"
  local rootfs="${WORK:?}/rootfs"
  local kver mod_src mod_dst rel copied=0

  kver="$(_rootfs_kver)"
  mod_src="$rootfs/lib/modules/$kver"
  mod_dst="$extra_root/usr/lib/modules/$kver"
  [[ -d "$mod_src" ]] || {
    echo "[4e/9] WARN: missing $mod_src — skipping WiFi module inject" >&2
    return 0
  }

  _copy_wifi_mod_tree() {
    local src_sub="$1"
    [[ -d "$mod_src/$src_sub" ]] || return 0
    mkdir -p "$mod_dst/$src_sub"
    cp -a "$mod_src/$src_sub/." "$mod_dst/$src_sub/"
    copied=1
  }

  _copy_wifi_mod_tree "kernel/drivers/net/wireless/realtek/rtw88"
  _copy_wifi_mod_tree "kernel/drivers/net/wireless/realtek/rtw89"
  _copy_wifi_mod_tree "kernel/drivers/net/wireless/intel/iwlwifi"
  _copy_wifi_mod_tree "kernel/drivers/net/wireless/broadcom/brcm80211"
  _copy_wifi_mod_tree "kernel/drivers/net/wireless/ath"
  _copy_wifi_mod_tree "kernel/drivers/net/wireless/mediatek"

  for rel in \
    kernel/net/mac80211/mac80211.ko.xz \
    kernel/net/wireless/cfg80211.ko.xz \
    kernel/net/rfkill/rfkill.ko.xz \
    kernel/lib/libarc4/libarc4.ko.xz; do
    [[ -f "$mod_src/$rel" ]] || continue
    mkdir -p "$mod_dst/$(dirname "$rel")"
    cp -a "$mod_src/$rel" "$mod_dst/$rel"
    copied=1
  done

  if (( copied )); then
    echo "[4e/9] Staged WiFi kernel modules for d-i initrd ($kver, $(du -sh "$mod_dst" | awk '{print $1}'))"
  else
    echo "[4e/9] WARN: no rtw88/rtw89 or 80211 modules found under $mod_src" >&2
  fi
}

embed_cogos_in_di_initrd() {
  local runtime_tar="${1:-${WORK:?}/iso/install/wolf-cog-os/runtime.tar}"
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local extra="${WORK}/tmp/cogos-di-initrd-extra"
  local late_src="$script_dir/../payload-iso/install/cogos-di-late-command.sh"
  local wifi_probe_src="$script_dir/../payload-iso/install/cogos-di-wifi-probe.sh"
  local netcfg_dispatch_src="$script_dir/../payload-iso/install/cogos-di-netcfg-dispatch.sh"
  local preseed_src="$script_dir/../payload-iso/install/preseed.cfg"
  local finish_src="${WORK}/rootfs/usr/local/bin/cogos-install-finish"

  [[ -f "$runtime_tar" ]] || {
    echo "ERROR: embed_cogos_in_di_initrd: missing $runtime_tar (run stage_di_iso_payload first)" >&2
    return 1
  }

  _assert_di_kver_match

  rm -rf "$extra"
  mkdir -p "$extra/cogos-hooks" "$extra/cogos-payload"
  _stage_di_initrd_wifi_firmware "$extra"
  _stage_di_initrd_wifi_modules "$extra"
  gzip -9 -c "$runtime_tar" > "$extra/cogos-payload/runtime.tar.gz"
  cp -f "$late_src" "$extra/cogos-hooks/cogos-di-late-command.sh"
  cp -f "$wifi_probe_src" "$extra/cogos-hooks/cogos-di-wifi-probe.sh"
  cp -f "$netcfg_dispatch_src" "$extra/cogos-hooks/cogos-di-netcfg-dispatch.sh"
  cp -f "$preseed_src" "$extra/preseed.cfg"
  chmod +x "$extra/cogos-hooks/cogos-di-late-command.sh" \
    "$extra/cogos-hooks/cogos-di-wifi-probe.sh" \
    "$extra/cogos-hooks/cogos-di-netcfg-dispatch.sh"
  if [[ -f "$finish_src" ]]; then
    cp -f "$finish_src" "$extra/cogos-hooks/cogos-install-finish"
    chmod +x "$extra/cogos-hooks/cogos-install-finish"
  fi

  local patched=0
  for initrd in \
    "${WORK}/iso/install/gtk/initrd.gz" \
    "${WORK}/iso/install/initrd.gz"; do
    [[ -f "$initrd" ]] || continue
    _embed_overlay_in_initrd "$initrd" "$extra" || continue
    patched=$((patched + 1))
    echo "[4e/9] CoGOS embedded in $(basename "$(dirname "$initrd")")/initrd.gz (+$(du -h "$initrd" | awk '{print $1}'))"
  done

  if (( patched == 0 )); then
    echo "ERROR: no gtk/text initrd.gz found under $WORK/iso/install/" >&2
    return 1
  fi
  echo "[4e/9] d-i initrd embed complete ($patched initrd images)"
}

_embed_overlay_in_initrd() {
  local initrd_gz="$1"
  local extra_dir="$2"
  local tmp="${WORK}/tmp/initrd-embed-$$"
  local root="$tmp/root"
  local raw="$tmp/initrd.raw"
  local backup="${initrd_gz}.orig"
  local kver

  mkdir -p "$root"
  if [[ ! -f "$backup" ]]; then
    cp -a "$initrd_gz" "$backup"
  fi

  gzip -dc "$backup" > "$raw"
  (
    cd "$root"
    cpio -idm --quiet < "$raw" 2>/dev/null || cpio -idm --quiet < "$raw"
  )

  if [[ -d "$extra_dir/lib" && ! -L "$root/lib" ]]; then
    echo "ERROR: overlay must not ship lib/ (breaks initrd lib -> usr/lib symlink)" >&2
    return 1
  fi

  for item in "$extra_dir"/*; do
    [[ -e "$item" ]] || continue
    case "$(basename "$item")" in
      usr) ;;
      *) cp -a "$item" "$root/" ;;
    esac
  done

  if [[ -f "$extra_dir/cogos-hooks/cogos-di-wifi-probe.sh" ]]; then
    mkdir -p "$root/lib/debian-installer/start.d"
    cp -a "$extra_dir/cogos-hooks/cogos-di-wifi-probe.sh" \
      "$root/lib/debian-installer/start.d/zz-cogos-wifi"
    chmod +x "$root/lib/debian-installer/start.d/zz-cogos-wifi"
  fi

  kver="$(_rootfs_kver)"
  _merge_wifi_overlay_into_initrd "$root" "$extra_dir" "$kver"

  if _initrd_modules_dir "$root" "$kver" >/dev/null; then
    if command -v depmod >/dev/null 2>&1; then
      depmod -b "$root" "$kver"
      echo "[4e/9] depmod refreshed for d-i initrd ($kver)"
    else
      echo "[4e/9] WARN: depmod missing — WiFi modules may not autoload in d-i" >&2
    fi
  else
    echo "[4e/9] WARN: initrd lacks lib/modules/$kver (rootfs=$kver)" >&2
  fi

  (
    cd "$root"
    find . -print0 | cpio --null -o -H newc --quiet | gzip -9 > "$initrd_gz"
  )
  rm -rf "$tmp"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  WORK="${COGOS_WORK:?}"
  embed_cogos_in_di_initrd "${1:-}"
fi
