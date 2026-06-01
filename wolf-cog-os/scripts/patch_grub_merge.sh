#!/usr/bin/env bash
# Merge GRUB: metal-style standalone cfg (no missing config.cfg); append governed entries.

# Debian live: iso/live/vmlinuz + iso/boot/grub/grub.cfg
# Fedora/Rocky: iso/images/pxeboot/* + iso/boot/grub2/grub.cfg (stock menu kept for forge repack)
resolve_grub_boot_paths() {
  local candidate

  GRUB_CFG=""
  VMLINUZ=""
  INITRD=""

  if [[ -d "$WORK/iso/live" ]]; then
    VMLINUZ="$(find "$WORK/iso/live" -maxdepth 1 -type f -name 'vmlinuz*' 2>/dev/null | sort | head -n 1)"
    INITRD="$(find "$WORK/iso/live" -maxdepth 1 -type f -name 'initrd*' 2>/dev/null | sort | head -n 1)"
    for candidate in "$WORK/iso/boot/grub/grub.cfg"; do
      if [[ -f "$candidate" ]]; then
        GRUB_CFG="$candidate"
        break
      fi
    done
  fi

  if [[ -z "$VMLINUZ" && -f "$WORK/iso/images/pxeboot/vmlinuz" ]]; then
    VMLINUZ="$WORK/iso/images/pxeboot/vmlinuz"
    INITRD="$WORK/iso/images/pxeboot/initrd.img"
    for candidate in \
      "$WORK/iso/boot/grub2/grub.cfg" \
      "$WORK/iso/EFI/BOOT/grub.cfg" \
      "$WORK/iso/boot/grub/grub.cfg"; do
      if [[ -f "$candidate" ]]; then
        GRUB_CFG="$candidate"
        break
      fi
    done
  fi

  [[ -n "$VMLINUZ" && -n "$INITRD" && -n "$GRUB_CFG" ]] || return 1
  VMLINUZ="/${VMLINUZ#$WORK/iso/}"
  INITRD="/${INITRD#$WORK/iso/}"
  return 0
}

is_fedora_family_iso_tree() {
  [[ -f "$WORK/iso/images/install.img" && -f "$WORK/iso/images/pxeboot/vmlinuz" ]]
}

patch_grub_merge() {
  local grub="$WORK/iso/boot/grub/grub.cfg"
  local isolinux="$WORK/iso/isolinux"
  local vmlinuz initrd menu_label
  local findiso_arg=""

  vmlinuz="$(find "$WORK/iso/live" -maxdepth 1 -type f -name 'vmlinuz*' 2>/dev/null | sort | head -n 1)"
  initrd="$(find "$WORK/iso/live" -maxdepth 1 -type f -name 'initrd*' 2>/dev/null | sort | head -n 1)"
  if [[ -z "$vmlinuz" || -z "$initrd" || ! -d "$WORK/iso/boot/grub" ]]; then
    echo "GRUB merge skipped; live kernel/initrd/grub not found." >&2
    return 0
  fi

  vmlinuz="/${vmlinuz#$WORK/iso/}"
  initrd="/${initrd#$WORK/iso/}"
  menu_label="${COGOS_OS_MENU:-Wolf CoG OS Master Boot}"

  if [[ "${COGOS_LIVE_FINDISO:-0}" == "1" ]]; then
    findiso_arg=" findiso=\${iso_path}"
  fi

  # Metal tree has no config.cfg — use self-contained grub like Wolf-CoG-OS-metal-fixed.
  cat > "$grub" <<EOF
set timeout=5
set default=0
terminal_output console
set gfxpayload=text

# Default: known-good metal live (nomodeset, no findiso, no verify-checksums).
menuentry "Wolf CoG OS Metal Fixed Live" --hotkey=l {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd nomodeset quiet
	initrd	$initrd
}

menuentry "${menu_label} — HP safe boot" --hotkey=h {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd nosplash loglevel=7 systemd.show_status=true plymouth.enable=0 console=tty0 console=ttyS0,115200n8 nomodeset i915.modeset=0 nouveau.modeset=0 radeon.modeset=0 cogos.safe=1 governance=off${findiso_arg}
	initrd	$initrd
}

menuentry "${menu_label} — Master Boot (governed full stack)" --hotkey=m {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd nosplash loglevel=4 systemd.show_status=true plymouth.enable=0 console=tty0 console=ttyS0,115200n8 nomodeset i915.modeset=0 nouveau.modeset=0 radeon.modeset=0 cogos.master=1 cogos.unified=1 cogos.metal=1 cogos.safe=1${findiso_arg}
	initrd	$initrd
}

menuentry "${menu_label} — governed live" {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd loglevel=4 systemd.show_status=true plymouth.enable=0 console=tty0 console=ttyS0,115200n8 nomodeset cogos.pid1.strict=0${findiso_arg}
	initrd	$initrd
}

menuentry "${menu_label} — recovery shell" --hotkey=r {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd nosplash loglevel=7 systemd.show_status=true plymouth.enable=0 console=tty0 console=ttyS0,115200n8 nomodeset cogos.recovery=1 cogos.safe=1${findiso_arg}
	initrd	$initrd
}

menuentry "${menu_label} — fail-safe compatibility" {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd memtest noapic noapm nodma nomce nosmp nosplash nomodeset vga=788 console=tty0 console=ttyS0,115200n8 cogos.safe=1 governance=off
	initrd	$initrd
}
EOF

  if [[ -f "$WORK/iso/boot/grub/install_start.cfg" && -f "$WORK/iso/boot/grub/install.cfg" ]]; then
    cat >> "$grub" <<'EOF'

if true; then
source	/boot/grub/install_start.cfg
submenu 'Wolf CoG OS installer ...' --hotkey=a {
	source	/boot/grub/install.cfg
}
fi
EOF
  fi

  cat >> "$grub" <<'EOF'

submenu 'Advanced options ...' {
	menuentry 'UEFI Firmware Settings' --hotkey=f {
		fwsetup
	}
}
EOF

  if [[ -d "$isolinux" && -f "$isolinux/live.cfg" ]]; then
    cat > "$isolinux/live.cfg" <<EOF
label cogos-metal-live
	menu label ^Wolf CoG OS Metal Fixed Live
	menu default
	linux /live/vmlinuz
	initrd /live/initrd
	append boot=live components init=/lib/systemd/systemd nomodeset quiet

label cogos-hp-safe
	menu label Wolf CoG OS - ^HP safe boot
	linux /live/vmlinuz
	initrd /live/initrd
	append boot=live components init=/lib/systemd/systemd nosplash loglevel=7 systemd.show_status=true plymouth.enable=0 console=tty0 console=ttyS0,115200n8 nomodeset i915.modeset=0 nouveau.modeset=0 radeon.modeset=0 cogos.safe=1 governance=off

label cogos-maste
	menu label Wolf CoG OS - ^Master Boot
	linux /live/vmlinuz
	initrd /live/initrd
	append boot=live components init=/lib/systemd/systemd nosplash loglevel=4 nomodeset i915.modeset=0 cogos.master=1 cogos.unified=1 cogos.metal=1 cogos.safe=1
EOF
  fi

  echo "GRUB merged: metal-style standalone cfg, default entry 0, no verify-checksums entry"
}

# Forge ISO profile: normal live, Forge Mode cockpit, and recovery shell.
patch_grub_forge() {
  local grub isolinux menu_label
  local findiso_arg=""
  local vmlinuz initrd

  if is_fedora_family_iso_tree; then
    echo "GRUB forge: Rocky/Fedora substrate — keeping stock grub.cfg (forge rootfs repacked into install.img)" >&2
    return 0
  fi

  if ! resolve_grub_boot_paths; then
    echo "GRUB forge patch skipped; live kernel/initrd/grub not found." >&2
    return 0
  fi

  grub="$GRUB_CFG"
  vmlinuz="$VMLINUZ"
  initrd="$INITRD"
  isolinux="$WORK/iso/isolinux"
  menu_label="${COGOS_OS_MENU:-Wolf CoG OS Forge}"

  if [[ "${COGOS_LIVE_FINDISO:-0}" == "1" ]]; then
    findiso_arg=" findiso=\${iso_path}"
  fi

  cat > "$grub" <<EOF
set timeout=8
set default=0
terminal_output console
set gfxpayload=text

menuentry "${menu_label} — Run CoGOS (Normal)" --hotkey=n {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd nomodeset quiet
	initrd	$initrd
}

menuentry "${menu_label} — Enter Forge Mode" --hotkey=f {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd nomodeset quiet cogos.forge=1 COGOS_FORGE_MODE=1${findiso_arg}
	initrd	$initrd
}

menuentry "${menu_label} — Recovery / Debug Shell" --hotkey=r {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd nosplash loglevel=7 systemd.show_status=true plymouth.enable=0 console=tty0 console=ttyS0,115200n8 nomodeset cogos.recovery=1 cogos.safe=1${findiso_arg}
	initrd	$initrd
}

submenu 'Advanced options ...' {
	menuentry 'UEFI Firmware Settings' --hotkey=u {
		fwsetup
	}
}
EOF

  if [[ -d "$isolinux" && -f "$isolinux/live.cfg" ]]; then
    cat > "$isolinux/live.cfg" <<EOF
label cogos-forge-normal
	menu label ^Run CoGOS (Normal)
	menu default
	linux /live/vmlinuz
	initrd /live/initrd
	append boot=live components init=/lib/systemd/systemd nomodeset quiet

label cogos-forge-mode
	menu label ^Enter Forge Mode
	linux /live/vmlinuz
	initrd /live/initrd
	append boot=live components init=/lib/systemd/systemd nomodeset quiet cogos.forge=1 COGOS_FORGE_MODE=1

label cogos-forge-recovery
	menu label ^Recovery / Debug Shell
	linux /live/vmlinuz
	initrd /live/initrd
	append boot=live components init=/lib/systemd/systemd nomodeset cogos.recovery=1 cogos.safe=1
EOF
  fi

  echo "GRUB forge: normal live + Forge Mode + recovery entries"
}

# Regular edition: proven live boot + cogos-install to disk (full runtime on first boot).
patch_grub_metal_installer() {
  local live_title="Wolf CoG OS — Live (recommended)"
  if [[ "${COGOS_FULL_RUNTIME:-0}" == "1" ]]; then
    live_title="Wolf CoG OS — Live (full runtime, recommended)"
  fi
  local grub="$WORK/iso/boot/grub/grub.cfg"
  local isolinux="$WORK/iso/isolinux"
  local vmlinuz initrd

  vmlinuz="$(find "$WORK/iso/live" -maxdepth 1 -type f -name 'vmlinuz*' 2>/dev/null | sort | head -n 1)"
  initrd="$(find "$WORK/iso/live" -maxdepth 1 -type f -name 'initrd*' 2>/dev/null | sort | head -n 1)"
  if [[ -z "$vmlinuz" || -z "$initrd" || ! -d "$WORK/iso/boot/grub" ]]; then
    echo "GRUB metal installer patch skipped; live kernel/initrd/grub not found." >&2
    return 0
  fi

  vmlinuz="/${vmlinuz#$WORK/iso/}"
  initrd="/${initrd#$WORK/iso/}"

  cat > "$grub" <<EOF
set timeout=8
set default=0
terminal_output console
set gfxpayload=text

menuentry "$live_title" --hotkey=l {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd nomodeset quiet
	initrd	$initrd
}

menuentry "Wolf CoG OS — Safe live (systemd bypass)" --hotkey=s {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd nomodeset quiet cogos.safe=1 governance=off
	initrd	$initrd
}

submenu 'Install Wolf CoG OS to disk ...' --hotkey=i {
	menuentry '1) Boot live (above), then run cogos-install from terminal' {
		linux	$vmlinuz boot=live components init=/lib/systemd/systemd nomodeset quiet
		initrd	$initrd
	}
	menuentry '2) Recovery / safe shell before install' {
		linux	$vmlinuz boot=live components init=/lib/systemd/systemd nomodeset cogos.recovery=1 cogos.safe=1
		initrd	$initrd
	}
}

submenu 'Advanced options ...' {
	menuentry 'UEFI Firmware Settings' --hotkey=f {
		fwsetup
	}
}
EOF

  if [[ -d "$isolinux" && -f "$isolinux/live.cfg" ]]; then
    cat > "$isolinux/live.cfg" <<EOF
label cogos-metal-live
	menu label ^Wolf CoG OS Live (full runtime)
	menu default
	linux /live/vmlinuz
	initrd /live/initrd
	append boot=live components init=/lib/systemd/systemd nomodeset quiet

label cogos-safe
	menu label Wolf CoG OS - ^Safe live
	linux /live/vmlinuz
	initrd /live/initrd
	append boot=live components init=/lib/systemd/systemd nomodeset quiet cogos.safe=1 governance=off
EOF
  fi

  echo "GRUB regular edition: live default + install submenu (full runtime)"
}

# Resolve live kernel/initrd paths on the extracted ISO tree.
resolve_iso_live_boot_paths() {
  LIVE_VMLINUZ=""
  LIVE_INITRD=""
  if ! resolve_grub_boot_paths; then
    return 1
  fi
  LIVE_VMLINUZ="$VMLINUZ"
  LIVE_INITRD="$INITRD"
  return 0
}

# Debian live: stock gtk d-i + Wolf preseed (full runtime via late_command on /install/).
patch_grub_debian_installer() {
  local grub="$WORK/iso/boot/grub/grub.cfg"
  local live_title="Wolf CoG OS — Live"
  if [[ "${COGOS_FULL_RUNTIME:-0}" == "1" ]]; then
    live_title="Wolf CoG OS — Live (full runtime)"
  fi

  resolve_iso_live_boot_paths || {
    echo "GRUB debian installer patch skipped; live kernel/initrd not found." >&2
    return 0
  }

  patch_debian_install_media_wolf

  cat > "$grub" <<EOF
set timeout=8
set default=1
terminal_output console
set gfxpayload=text

menuentry "$live_title" --hotkey=l {
	linux	$LIVE_VMLINUZ boot=live components init=/lib/systemd/systemd nomodeset quiet
	initrd	$LIVE_INITRD
}
EOF

  if [[ -f "$WORK/iso/boot/grub/install_start.cfg" && -f "$WORK/iso/boot/grub/install.cfg" ]]; then
    cat >> "$grub" <<'EOF'

if true; then
source	/boot/grub/install_start.cfg
submenu 'Wolf CoG OS advanced install ...' --hotkey=a {
	source /boot/grub/theme.cfg
	source	/boot/grub/install.cfg
}
fi
EOF
  fi

  cat >> "$grub" <<EOF

menuentry "Wolf CoG OS — Safe live" --hotkey=s {
	linux	$LIVE_VMLINUZ boot=live components init=/lib/systemd/systemd nomodeset quiet cogos.safe=1 governance=off
	initrd	$LIVE_INITRD
}

submenu 'Terminal install (cogos-install) ...' --hotkey=t {
	menuentry 'Boot live, then run cogos-install apply' {
		linux	$LIVE_VMLINUZ boot=live components init=/lib/systemd/systemd nomodeset quiet
		initrd	$LIVE_INITRD
	}
}

submenu 'Advanced options ...' {
	menuentry 'UEFI Firmware Settings' --hotkey=f {
		fwsetup
	}
}
EOF

  if [[ -d "$WORK/iso/isolinux" && -f "$WORK/iso/isolinux/live.cfg" ]]; then
    cat > "$WORK/iso/isolinux/live.cfg" <<EOF
label live
	menu label ^Wolf CoG OS Live (full runtime)
	linux /live/vmlinuz
	initrd /live/initrd.img
	append boot=live components init=/lib/systemd/systemd nomodeset quiet

label safe
	menu label Wolf CoG OS Safe live
	linux /live/vmlinuz
	initrd /live/initrd.img
	append boot=live components init=/lib/systemd/systemd nomodeset quiet cogos.safe=1 governance=off
EOF
  fi

  echo "GRUB debian installer: gtk d-i (default) + Wolf preseed + isolinux live"
}

# Universal installer ISO: metal-safe live defaults plus optional Calamares surprise path.
patch_grub_universal_installer() {
  local grub="$WORK/iso/boot/grub/grub.cfg"
  local isolinux="$WORK/iso/isolinux"
  local vmlinuz initrd
  local calamares_available="${COGOS_CALAMARES_AVAILABLE:-1}"

  vmlinuz="$(find "$WORK/iso/live" -maxdepth 1 -type f -name 'vmlinuz*' 2>/dev/null | sort | head -n 1)"
  initrd="$(find "$WORK/iso/live" -maxdepth 1 -type f -name 'initrd*' 2>/dev/null | sort | head -n 1)"
  if [[ -z "$vmlinuz" || -z "$initrd" || ! -d "$WORK/iso/boot/grub" ]]; then
    echo "GRUB universal patch skipped; live kernel/initrd/grub not found." >&2
    return 0
  fi

  vmlinuz="/${vmlinuz#$WORK/iso/}"
  initrd="/${initrd#$WORK/iso/}"

  cat > "$grub" <<EOF
set timeout=8
set default=0
terminal_output console
set gfxpayload=text

menuentry "Wolf CoG OS — Live (metal baseline, recommended)" --hotkey=l {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd nomodeset quiet
	initrd	$initrd
}

menuentry "Wolf CoG OS — Live safe mode" --hotkey=s {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd nomodeset quiet cogos.safe=1 governance=off
	initrd	$initrd
}

submenu "Install Wolf CoG OS (Metal path - primary) ..." --hotkey=m {
	menuentry "Boot live, then run cogos-install apply" {
		linux	$vmlinuz boot=live components init=/lib/systemd/systemd nomodeset quiet
		initrd	$initrd
	}
	menuentry "Recovery shell before metal install" {
		linux	$vmlinuz boot=live components init=/lib/systemd/systemd nomodeset cogos.recovery=1 cogos.safe=1
		initrd	$initrd
	}
}
EOF

  if [[ "$calamares_available" == "1" && -f "$WORK/iso/boot/grub/install_start.cfg" && -f "$WORK/iso/boot/grub/install.cfg" ]]; then
    cat >> "$grub" <<EOF
menuentry "Install Wolf CoG OS (Graphical Calamares)" --hotkey=c {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd nomodeset quiet cogos.calamares=1
	initrd	$initrd
}

submenu "Legacy Debian gtk/text installer (no CoGOS hook) ..." --hotkey=d {
	source	/boot/grub/install_start.cfg
	source	/boot/grub/install.cfg
}
EOF
  else
    cat >> "$grub" <<EOF
menuentry "Install Wolf CoG OS (Surprise path unavailable - use Metal path)" --hotkey=c {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd nomodeset quiet cogos.install_hint=1
	initrd	$initrd
}
EOF
  fi

  cat >> "$grub" <<EOF

submenu "Install guidance ..." --hotkey=g {
	menuentry "Open live terminal then run: cogos-install plan --target /dev/sdX" {
		linux	$vmlinuz boot=live components init=/lib/systemd/systemd nomodeset quiet cogos.install_hint=1
		initrd	$initrd
	}
	menuentry "Apply install: cogos-install apply --target /dev/sdX --yes --confirm-erase sdX" {
		linux	$vmlinuz boot=live components init=/lib/systemd/systemd nomodeset quiet cogos.install_hint=1
		initrd	$initrd
	}
}

submenu "Advanced options ..." {
	menuentry "UEFI Firmware Settings" --hotkey=f {
		fwsetup
	}
}
EOF

  if [[ -d "$isolinux" && -f "$isolinux/live.cfg" ]]; then
    cat > "$isolinux/live.cfg" <<EOF
label cogos-universal-live
	menu label ^Wolf CoG OS Live (metal baseline)
	menu default
	linux /live/vmlinuz
	initrd /live/initrd
	append boot=live components init=/lib/systemd/systemd nomodeset quiet

label cogos-universal-safe
	menu label Wolf CoG OS - ^Live safe mode
	linux /live/vmlinuz
	initrd /live/initrd
	append boot=live components init=/lib/systemd/systemd nomodeset quiet cogos.safe=1 governance=off

label cogos-install-guidance
	menu label Wolf CoG OS - Install ^guidance (metal path)
	linux /live/vmlinuz
	initrd /live/initrd
	append boot=live components init=/lib/systemd/systemd nomodeset quiet cogos.install_hint=1
EOF
  fi

  if [[ "$calamares_available" == "1" ]]; then
    echo "GRUB universal installer: metal path + Calamares surprise path"
  else
    echo "GRUB universal installer: Calamares missing -> metal path + fallback guidance"
  fi
}

# Surprise daily-driver ISO: stock Debian live UX; CoGOS takeover on first disk boot.
patch_grub_surprise() {
  local grub="$WORK/iso/boot/grub/grub.cfg"
  local isolinux="$WORK/iso/isolinux"
  local vmlinuz initrd
  local findiso_dd="" findiso_vt=" findiso=\${iso_path}"

  vmlinuz="$(find "$WORK/iso/live" -maxdepth 1 -type f -name 'vmlinuz*' 2>/dev/null | sort | head -n 1)"
  initrd="$(find "$WORK/iso/live" -maxdepth 1 -type f -name 'initrd*' 2>/dev/null | sort | head -n 1)"
  if [[ -z "$vmlinuz" || -z "$initrd" || ! -d "$WORK/iso/boot/grub" ]]; then
    echo "GRUB surprise patch skipped; live kernel/initrd/grub not found." >&2
    return 0
  fi

  vmlinuz="/${vmlinuz#$WORK/iso/}"
  initrd="/${initrd#$WORK/iso/}"

  if [[ -f "$WORK/iso/boot/grub/live.cfg" ]]; then
    cp -f "$WORK/iso/boot/grub/live.cfg" "$grub"
    sed -i 's/^set default=.*/set default=0/' "$grub" 2>/dev/null || true
  else
    cat > "$grub" <<EOF
set timeout=10
set default=0
terminal_output console
set gfxpayload=text

menuentry "Live system (amd64)" --hotkey=l {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd quiet${findiso_dd}
	initrd	$initrd
}

menuentry "Live system (amd64) — Ventoy/Rufus ISO" {
	linux	$vmlinuz boot=live components init=/lib/systemd/systemd quiet${findiso_vt}
	initrd	$initrd
}
EOF
  fi

  if [[ -f "$WORK/iso/boot/grub/install_start.cfg" && -f "$WORK/iso/boot/grub/install.cfg" ]]; then
    cat >> "$grub" <<'EOF'

if true; then
source	/boot/grub/install_start.cfg
submenu 'Install Debian (graphical/text) ...' --hotkey=i {
	source	/boot/grub/install.cfg
}
fi
EOF
  fi

  cat >> "$grub" <<EOF

submenu 'CoGOS recovery (hidden) ...' --hotkey=r {
	menuentry 'Recovery shell (safe mode)' {
		linux	$vmlinuz boot=live components init=/lib/systemd/systemd nosplash nomodeset cogos.recovery=1 cogos.safe=1${findiso_dd}
		initrd	$initrd
	}
	menuentry 'HP safe live (no PID1 gate)' {
		linux	$vmlinuz boot=live components init=/lib/systemd/systemd nosplash nomodeset modprobe.blacklist=hp_bioscfg cogos.safe=1 governance=off${findiso_dd}
		initrd	$initrd
	}
}

submenu 'Advanced options ...' {
	menuentry 'UEFI Firmware Settings' --hotkey=f {
		fwsetup
	}
}
EOF

  if [[ -d "$isolinux" && -f "$isolinux/live.cfg" ]]; then
    if ! grep -q 'findiso=' "$isolinux/live.cfg" 2>/dev/null; then
      cat >> "$isolinux/live.cfg" <<EOF

label live-ventoy
	menu label Live system (Ventoy findiso)
	linux /live/vmlinuz
	initrd /live/initrd
	append boot=live components init=/lib/systemd/systemd quiet findiso=\${iso_path}
EOF
    fi
  fi

  echo "GRUB surprise: stock Debian live default, install submenu, Ventoy findiso entry"
}
