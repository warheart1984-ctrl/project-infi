#!/usr/bin/env bash
# Debian/apt chroot customization (production).
set -euo pipefail

backend_chroot_customize() {
  local rootfs_out="$1"
  cat >"$rootfs_out/tmp/cogos-chroot-setup.sh" <<'CHROOT_EOF'
#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export TMPDIR=/tmp
mkdir -p /tmp

PKG_FILE="/tmp/cogos-packages.txt"
if [[ ! -s "$PKG_FILE" ]]; then
  echo "ERROR: package list is empty at $PKG_FILE" >&2
  exit 1
fi

apt-get -o Acquire::Retries=5 -o Acquire::By-Hash=yes update
PKGS="$(tr '\n' ' ' <"$PKG_FILE")"
if ! apt-get install -y --fix-missing --no-install-recommends $PKGS; then
  echo "WARN: initial apt install failed; attempting dpkg/apt recovery" >&2
  dpkg --configure -a || true
  apt-get -f install -y || true
  apt-get install -y --fix-missing --no-install-recommends $PKGS
fi

echo "$COGOS_HOSTNAME" >/etc/hostname
printf '127.0.0.1\tlocalhost\n127.0.1.1\t%s\n' "$COGOS_HOSTNAME" >/etc/hosts

if [[ ! -e "/usr/share/zoneinfo/$COGOS_TIMEZONE" ]]; then
  echo "WARNING: timezone $COGOS_TIMEZONE not found, using UTC" >&2
  COGOS_TIMEZONE="UTC"
fi
ln -snf "/usr/share/zoneinfo/$COGOS_TIMEZONE" /etc/localtime
echo "$COGOS_TIMEZONE" >/etc/timezone
dpkg-reconfigure -f noninteractive tzdata || true

if ! grep -q "^${COGOS_LOCALE} UTF-8$" /etc/locale.gen; then
  echo "${COGOS_LOCALE} UTF-8" >>/etc/locale.gen
fi
locale-gen "$COGOS_LOCALE"
update-locale LANG="$COGOS_LOCALE"

if [[ -n "$COGOS_DEFAULT_USER" ]]; then
  if ! id "$COGOS_DEFAULT_USER" >/dev/null 2>&1; then
    if getent group "$COGOS_DEFAULT_USER" >/dev/null 2>&1; then
      useradd -m -s /bin/bash -g "$COGOS_DEFAULT_USER" "$COGOS_DEFAULT_USER" || \
        useradd -m -s /bin/bash -N "$COGOS_DEFAULT_USER"
    else
      useradd -m -s /bin/bash "$COGOS_DEFAULT_USER"
    fi
  fi
  usermod -aG sudo "$COGOS_DEFAULT_USER" || true
  if [[ -n "${COGOS_DEFAULT_PASSWORD:-}" ]]; then
    echo "${COGOS_DEFAULT_USER}:${COGOS_DEFAULT_PASSWORD}" | chpasswd
  else
    passwd -d "$COGOS_DEFAULT_USER" >/dev/null 2>&1 || true
  fi
fi

apt-get clean
rm -rf /var/lib/apt/lists/*
truncate -s 0 /etc/machine-id || true
rm -f /var/log/*.log /var/log/*/*.log 2>/dev/null || true
CHROOT_EOF

  chmod +x "$rootfs_out/tmp/cogos-chroot-setup.sh"
  chroot "$rootfs_out" /usr/bin/env \
    TMPDIR=/tmp \
    COGOS_HOSTNAME="${COGOS_HOSTNAME:-wolf-cog-os}" \
    COGOS_LOCALE="${COGOS_LOCALE:-en_US.UTF-8}" \
    COGOS_TIMEZONE="${COGOS_TIMEZONE:-UTC}" \
    COGOS_DEFAULT_USER="${COGOS_DEFAULT_USER:-operator}" \
    COGOS_DEFAULT_PASSWORD="${COGOS_DEFAULT_PASSWORD:-}" \
    bash /tmp/cogos-chroot-setup.sh
}
