#!/usr/bin/env bash
# Brand the live squashfs session as Wolf CoG OS and wire gtk d-i install from desktop.
set -euo pipefail

patch_live_wolf_branding() {
  local rootfs="${1:-$WORK/rootfs}"
  local tag="${COGOS_TAG:-wolf-cog-os}"
  local build_date="${COGOS_BUILD_DATE:-$(date -u +%Y-%m-%d)}"
  local os_release="$rootfs/etc/os-release"
  local issue="$rootfs/etc/issue"
  local hostname="$rootfs/etc/hostname"

  [[ -f "$os_release" ]] || {
    echo "WARN: patch_live_wolf_branding: missing $os_release" >&2
    return 0
  }

  python3 <<PY
from pathlib import Path

os_release = Path(r"$os_release")
tag = "$tag"
build_date = "$build_date"
lines = []
for line in os_release.read_text(encoding="utf-8").splitlines():
    if line.startswith("PRETTY_NAME="):
        lines.append(f'PRETTY_NAME="Wolf CoG OS {tag} (live session)"')
    elif line.startswith("NAME="):
        lines.append('NAME="Wolf CoG OS"')
    elif line.startswith("VERSION="):
        lines.append(f'VERSION="{tag} ({build_date})"')
    else:
        lines.append(line)
extra = {
    "COGOS_PRODUCT": "Wolf CoG OS",
    "COGOS_RELEASE": tag,
    "COGOS_BUILD_DATE": build_date,
    "COGOS_LIVE": "1",
}
for key, val in extra.items():
    needle = f"{key}="
    if not any(l.startswith(needle) for l in lines):
        lines.append(f'{key}="{val}"')
os_release.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

  printf 'Wolf CoG OS %s live session\\n \\l\n' "$tag" > "$issue"
  printf 'wolf-cog-os-live\n' > "$hostname"

  mkdir -p "$rootfs/etc/xdg/cogos"
  cat > "$rootfs/etc/xdg/cogos/live-branding.env" <<EOF
COGOS_PRODUCT=Wolf CoG OS
COGOS_RELEASE=$tag
COGOS_BUILD_DATE=$build_date
EOF

  echo "[4d/9] Live session branded: Wolf CoG OS ($tag)"
}

install_di_live_desktop() {
  local rootfs="${1:-$WORK/rootfs}"
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local launcher="$rootfs/usr/local/bin/cogos-launch-di-installer"
  local app="$rootfs/usr/share/applications/wolf-cog-os-install-di.desktop"
  local welcome="$rootfs/etc/xdg/autostart/cogos-live-welcome.desktop"
  local icon_autostart="$rootfs/etc/xdg/autostart/cogos-live-install-icon.desktop"
  local stock_install="$rootfs/usr/share/applications/calamares-install-debian.desktop"

  mkdir -p "$(dirname "$launcher")" "$(dirname "$app")" "$(dirname "$welcome")"

  if [[ -f "$script_dir/../payload/usr/local/bin/cogos-launch-di-installer" ]]; then
    cp -f "$script_dir/../payload/usr/local/bin/cogos-launch-di-installer" "$launcher"
  fi
  chmod +x "$launcher"

  if [[ -f "$stock_install" ]] && ! grep -q '^Hidden=true' "$stock_install" 2>/dev/null; then
    python3 <<PY
from pathlib import Path
path = Path(r"$stock_install")
text = path.read_text(encoding="utf-8")
if "Hidden=true" not in text:
    path.write_text(text.rstrip() + "\nHidden=true\n", encoding="utf-8")
PY
  fi

  cat > "$app" <<'EOF'
[Desktop Entry]
Type=Application
Name=Install Wolf CoG OS
GenericName=Graphical Installer
Comment=Reboot into the Wolf CoG OS gtk installer (full runtime on disk)
Exec=/usr/local/bin/cogos-launch-di-installer
Icon=system-installer
Terminal=false
Categories=System;
Keywords=install;wolf;cogos;debian;installer;
StartupNotify=true
EOF

  cat > "$welcome" <<'EOF'
[Desktop Entry]
Type=Application
Name=Wolf CoG OS live welcome
Exec=/usr/local/bin/cogos-live-welcome
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=8
NoDisplay=true
EOF

  cat > "$icon_autostart" <<'EOF'
[Desktop Entry]
Type=Application
Name=Wolf CoG OS install icon
Exec=sh -c 'for d in /home/live/Desktop /home/debian/Desktop /root/Desktop; do [ -d "$d" ] || continue; cp -f /usr/share/applications/wolf-cog-os-install-di.desktop "$d/Install Wolf CoG OS.desktop" 2>/dev/null || true; chmod +x "$d/Install Wolf CoG OS.desktop" 2>/dev/null || true; done'
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=3
NoDisplay=true
EOF

  cat > "$rootfs/usr/local/bin/cogos-live-welcome" <<'EOF'
#!/bin/sh
set -eu
STAMP=/run/cogos-live-welcome.stamp
[ -f "$STAMP" ] && exit 0
touch "$STAMP"
if [ -z "${DISPLAY:-}" ] && [ -S /tmp/.X11-unix/X0 ]; then
  export DISPLAY=:0
fi
[ -n "${DISPLAY:-}" ] || exit 0
if command -v zenity >/dev/null 2>&1; then
  zenity --info --title="Wolf CoG OS" --width=420 \
    --text="Welcome to Wolf CoG OS live.\n\n• Install (recommended): desktop icon → Live install from session\n• Or reboot to gtk installer from the same menu\n• Terminal: sudo cogos-install apply --target /dev/sdX --yes --confirm-erase sdX" \
    2>/dev/null || true
fi
EOF
  chmod +x "$rootfs/usr/local/bin/cogos-live-welcome"

  echo "[4d/9] Live desktop: Install Wolf CoG OS icon + welcome (live install + gtk reboot)"
}
