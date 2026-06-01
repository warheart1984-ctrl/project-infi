#!/usr/bin/env bash
# Patch Debian live GRUB + isolinux installer configs for Wolf CoG OS d-i + preseed.
set -euo pipefail

WOLF_DI_PRESEED="${WOLF_DI_PRESEED:-preseed/file=/preseed.cfg}"
WOLF_DI_FIRMWARE_KCL="${WOLF_DI_FIRMWARE_KCL:-firmware=1}"

patch_grub_linux_line() {
  local line="$1"
  if [[ "$line" != *"/install/"* ]]; then
    printf '%s' "$line"
    return
  fi
  if [[ "$line" == *"$WOLF_DI_PRESEED"* ]]; then
    printf '%s' "$line"
    return
  fi
  if [[ "$line" == *" ---"* ]]; then
    printf '%s' "${line/ --- / ${WOLF_DI_PRESEED} --- }"
    return
  fi
  printf '%s %s' "$line" "$WOLF_DI_PRESEED"
}

patch_grub_install_cfg_file() {
  local cfg="$1"
  [[ -f "$cfg" ]] || return 0
  python3 <<PY
from pathlib import Path
import re

cfg = Path(r"$cfg")
preseed = "$WOLF_DI_PRESEED"
fw_kcl = "$WOLF_DI_FIRMWARE_KCL"
text = cfg.read_text(encoding="utf-8")
text = text.replace("Graphical installer", "Wolf CoG OS graphical installer")
text = text.replace("Text installer", "Wolf CoG OS text installer")
text = text.replace("Start installer", "Start Wolf CoG OS installer")
text = text.replace("Install Debian (graphical/text)", "Install Wolf CoG OS (graphical/text)")

lines = []
for line in text.splitlines(keepends=True):
    if "/install/gtk/vmlinuz" in line or "/install/vmlinuz" in line:
        if preseed not in line:
            if " ---" in line:
                line = line.replace(" --- ", f" {preseed} --- ", 1)
            elif line.rstrip().endswith("quiet"):
                line = line.rstrip()[:-5] + f" {preseed} quiet\n"
            else:
                line = line.rstrip() + f" {preseed}\n"
        if fw_kcl and fw_kcl not in line:
            if " ---" in line:
                line = line.replace(" --- ", f" {fw_kcl} --- ", 1)
            else:
                line = line.rstrip() + f" {fw_kcl}\n"
    lines.append(line)
cfg.write_text("".join(lines), encoding="utf-8")
print(f"patched GRUB installer cfg: {cfg}")
PY
}

patch_isolinux_install_cfg() {
  local cfg="$1"
  [[ -f "$cfg" ]] || return 0
  python3 <<PY
from pathlib import Path

cfg = Path(r"$cfg")
preseed = "$WOLF_DI_PRESEED"
fw_kcl = "$WOLF_DI_FIRMWARE_KCL"
text = cfg.read_text(encoding="utf-8")
text = text.replace("Graphical installer", "Wolf CoG OS graphical installer")
text = text.replace("Text installer", "Wolf CoG OS text installer")
text = text.replace("Start installer", "Start Wolf CoG OS installer")
text = text.replace("Advanced install options", "Wolf CoG OS advanced install")

lines = []
for line in text.splitlines(keepends=True):
    if line.strip().startswith("append ") and preseed not in line:
        if " ---" in line:
            line = line.replace(" --- ", f" {preseed} --- ", 1)
        else:
            line = line.rstrip() + f" {preseed}\n"
    if line.strip().startswith("append ") and fw_kcl and fw_kcl not in line:
        if " ---" in line:
            line = line.replace(" --- ", f" {fw_kcl} --- ", 1)
        else:
            line = line.rstrip() + f" {fw_kcl}\n"
    lines.append(line)
cfg.write_text("".join(lines), encoding="utf-8")
print(f"patched isolinux installer cfg: {cfg}")
PY
}

patch_install_start_for_wolf_di() {
  local start_cfg="${WORK}/iso/boot/grub/install_start.cfg"
  [[ -f "$start_cfg" ]] || return 0

  cat > "$start_cfg" <<EOF
menuentry 'Start Wolf CoG OS installer' --hotkey=i {
	linux	/install/gtk/vmlinuz vga=788 ${WOLF_DI_FIRMWARE_KCL} ${WOLF_DI_PRESEED} --- quiet
	initrd	/install/gtk/initrd.gz
}

menuentry 'Start Wolf CoG OS installer (speech synthesis)' --hotkey=s {
	linux	/install/gtk/vmlinuz speakup.synth=soft vga=788 ${WOLF_DI_FIRMWARE_KCL} ${WOLF_DI_PRESEED} --- quiet
	initrd	/install/gtk/initrd.gz
}
EOF
  echo "GRUB install_start.cfg: stock gtk d-i + Wolf CoG OS preseed hook"
}

patch_debian_install_media_wolf() {
  patch_install_start_for_wolf_di
  patch_grub_install_cfg_file "${WORK}/iso/boot/grub/install.cfg"
  patch_isolinux_install_cfg "${WORK}/iso/isolinux/install.cfg"
  echo "Debian install media patched: gtk/text d-i + full runtime late_command"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "Run from build.sh with WORK set" >&2
  exit 2
fi
