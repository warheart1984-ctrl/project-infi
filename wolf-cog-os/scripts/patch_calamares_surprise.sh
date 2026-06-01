#!/usr/bin/env bash
# Wire CoGOS install-finish into Debian live Calamares (graphical installer).
patch_calamares_surprise() {
  local rootfs="${1:-$WORK/rootfs}"
  local settings="$rootfs/etc/calamares/settings.conf"
  local module="$rootfs/etc/calamares/modules/shellprocess@cogos-finish.conf"

  if [[ ! -f "$settings" ]]; then
    echo "WARN: Calamares settings.conf missing; skipping surprise install hook" >&2
    return 0
  fi

  mkdir -p "$(dirname "$module")"
  cat > "$module" <<'EOF'
---
# Runs inside target chroot before umount — enables CoGOS on disk for first reboot.
script:
  - command: "/usr/local/bin/cogos-install-finish --in-target --quiet"
    timeout: 300
EOF

  if grep -q 'shellprocess@cogos-finish' "$settings"; then
    echo "[4e/8] Calamares hook already present: shellprocess@cogos-finish"
    return 0
  fi

  if ! grep -q '^  - umount$' "$settings"; then
    echo "WARN: Calamares settings.conf missing expected umount job; skipping surprise install hook patch" >&2
    return 0
  fi

  python3 <<PY
from pathlib import Path
settings = Path("$settings")
text = settings.read_text(encoding="utf-8")
needle = "  - umount\n"
insert = "  - shellprocess@cogos-finish\n  - umount\n"
if "shellprocess@cogos-finish" in text:
    raise SystemExit(0)
settings.write_text(text.replace(needle, insert, 1), encoding="utf-8")
print("patched Calamares exec sequence")
PY

  echo "[4e/8] Calamares post-install hook: shellprocess@cogos-finish (cogos-install-finish)"
}

# Launch Calamares from live desktop (GRUB Start installer or desktop icon).
install_calamares_live_autostart() {
  local rootfs="${1:-$WORK/rootfs}"
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local wrapper="$rootfs/usr/local/bin/cogos-calamares-if-requested"
  local launcher="$rootfs/usr/local/bin/cogos-launch-installer"
  local autostart="$rootfs/etc/xdg/autostart/cogos-calamares-if-requested.desktop"
  local app="$rootfs/usr/share/applications/wolf-cog-os-install.desktop"
  local icon_autostart="$rootfs/etc/xdg/autostart/cogos-live-install-icon.desktop"

  mkdir -p "$(dirname "$wrapper")" "$(dirname "$autostart")" "$(dirname "$app")"

  if [[ -f "$script_dir/../payload/usr/local/bin/cogos-launch-installer" ]]; then
    cp -f "$script_dir/../payload/usr/local/bin/cogos-launch-installer" "$launcher"
  elif [[ -f "${REPO_ROOT:-}/wolf-cog-os/payload/usr/local/bin/cogos-launch-installer" ]]; then
    cp -f "${REPO_ROOT}/wolf-cog-os/payload/usr/local/bin/cogos-launch-installer" "$launcher"
  else
    cp -f "$wrapper" "$launcher" 2>/dev/null || true
  fi

  cat > "$wrapper" <<'EOF'
#!/bin/sh
exec /usr/local/bin/cogos-launch-installer
EOF
  chmod +x "$wrapper" "$launcher"

  cat > "$autostart" <<'EOF'
[Desktop Entry]
Type=Application
Name=Install Wolf CoG OS (Calamares)
Comment=Graphical installer with CoGOS post-install hook
Exec=/usr/local/bin/cogos-launch-installer
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=6
NoDisplay=true
EOF

  cat > "$app" <<'EOF'
[Desktop Entry]
Type=Application
Name=Install Wolf CoG OS
Comment=Graphical disk installer (Calamares)
Exec=/usr/local/bin/cogos-launch-installer
Icon=system-installer
Terminal=false
Categories=System;
EOF

  cat > "$icon_autostart" <<'EOF'
[Desktop Entry]
Type=Application
Name=Wolf CoG OS install icon
Exec=sh -c 'for d in /home/live/Desktop /home/debian/Desktop /root/Desktop; do [ -d "$d" ] || continue; cp -f /usr/share/applications/wolf-cog-os-install.desktop "$d/Install Wolf CoG OS.desktop" 2>/dev/null || true; done; add-calamares-desktop-icon 2>/dev/null || true'
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=2
NoDisplay=true
EOF

  echo "[4e/8] Calamares live installer wired (GRUB Start installer + desktop icon + autostart)"
}
