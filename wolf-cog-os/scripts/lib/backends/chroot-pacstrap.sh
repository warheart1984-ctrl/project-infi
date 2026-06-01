#!/usr/bin/env bash
# Arch/pacman chroot customization (P11 production when pacstrap backend active).
set -euo pipefail

backend_chroot_customize() {
  local rootfs_out="$1"
  cat >"$rootfs_out/tmp/cogos-chroot-setup.sh" <<'CHROOT_EOF'
#!/usr/bin/env bash
set -euo pipefail
export TMPDIR=/tmp
mkdir -p /tmp

PKG_FILE="/tmp/cogos-packages.txt"
if [[ ! -s "$PKG_FILE" ]]; then
  echo "ERROR: package list is empty at $PKG_FILE" >&2
  exit 1
fi

pacman-key --init 2>/dev/null || true
pacman-key --populate archlinux 2>/dev/null || true
pacman -Sy --noconfirm
mapfile -t PKGS < <(grep -v '^#' "$PKG_FILE" | awk 'NF {print $1}')
if ((${#PKGS[@]} == 0)); then
  echo "ERROR: no packages parsed from $PKG_FILE" >&2
  exit 1
fi
pacman -S --needed --noconfirm "${PKGS[@]}"

echo "$COGOS_HOSTNAME" >/etc/hostname
printf '127.0.0.1\tlocalhost\n127.0.1.1\t%s\n' "$COGOS_HOSTNAME" >/etc/hosts
ln -snf "/usr/share/zoneinfo/${COGOS_TIMEZONE:-UTC}" /etc/localtime 2>/dev/null || true
hwclock --systohc 2>/dev/null || true

if [[ -n "$COGOS_DEFAULT_USER" ]]; then
  if ! id "$COGOS_DEFAULT_USER" >/dev/null 2>&1; then
    useradd -m -G wheel -s /bin/bash "$COGOS_DEFAULT_USER"
  fi
  if [[ -n "${COGOS_DEFAULT_PASSWORD:-}" ]]; then
    echo "${COGOS_DEFAULT_USER}:${COGOS_DEFAULT_PASSWORD}" | chpasswd
  fi
fi

pacman -Scc --noconfirm 2>/dev/null || true
truncate -s 0 /etc/machine-id || true
CHROOT_EOF

  chmod +x "$rootfs_out/tmp/cogos-chroot-setup.sh"
  cp "$rootfs_out/etc/resolv.conf" "$rootfs_out/etc/resolv.conf.bak" 2>/dev/null || true
  arch-chroot "$rootfs_out" /usr/bin/env \
    COGOS_HOSTNAME="${COGOS_HOSTNAME:-wolf-cog-arch}" \
    COGOS_TIMEZONE="${COGOS_TIMEZONE:-UTC}" \
    COGOS_DEFAULT_USER="${COGOS_DEFAULT_USER:-operator}" \
    COGOS_DEFAULT_PASSWORD="${COGOS_DEFAULT_PASSWORD:-}" \
    bash /tmp/cogos-chroot-setup.sh
}
