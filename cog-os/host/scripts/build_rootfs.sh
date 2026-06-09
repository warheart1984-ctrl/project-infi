#!/usr/bin/env bash
# Build a debootstrap rootfs with Nova NorthStar CoG OS host overlay (called by forge wrapper).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$HOST_DIR/../.." && pwd)"

ROOTFS="${1:-${ROOTFS:-$REPO_ROOT/artifacts/cog-os/rootfs-metal}}"
COG_PROFILE="${COG_PROFILE:-metal}"
DEBIAN_SUITE="${DEBIAN_SUITE:-bookworm}"
DEBIAN_MIRROR="${DEBIAN_MIRROR:-http://deb.debian.org/debian}"
ARCH="${ARCH:-amd64}"

INCLUDE_FILE="${COG_PACKAGE_LIST:-}"
EXCLUDE_SYSTEMD="${COG_EXCLUDE_SYSTEMD:-0}"

mkdir -p "$(dirname "$ROOTFS")"

rootfs_fstype() {
  local path="$1"
  local probe="$path"
  while [[ ! -e "$probe" && "$probe" != "/" ]]; do
    probe="$(dirname "$probe")"
  done
  local fstype=""
  if command -v findmnt >/dev/null 2>&1; then
    fstype="$(findmnt -no FSTYPE --target "$probe" 2>/dev/null || true)"
  fi
  if [[ -z "$fstype" ]]; then
    fstype="$(df -T "$probe" 2>/dev/null | awk 'NR==2 {print $2}')"
  fi
  echo "$fstype"
}

rootfs_on_foreign_fs() {
  local path="$1"
  case "$(rootfs_fstype "$path")" in
    9p|drvfs|fuse|fuseblk|vfat|ntfs|exfat|CIFS|cifs) return 0 ;;
  esac
  [[ "$path" == /mnt/* ]] && return 0
  return 1
}

WORK_ROOTFS="$ROOTFS"
SYNC_TO_ARTIFACT=0
if rootfs_on_foreign_fs "$ROOTFS"; then
  WORK_ROOTFS="${COG_ROOTFS_NATIVE:-/var/tmp/cog-os/$(basename "$ROOTFS")}"
  SYNC_TO_ARTIFACT=1
  echo "rootfs target is on $(rootfs_fstype "$ROOTFS"); debootstrap uses native path: $WORK_ROOTFS"
  rm -rf "$WORK_ROOTFS"
  mkdir -p "$WORK_ROOTFS"
fi

if [[ ! -d "$WORK_ROOTFS/usr" ]]; then
  echo "debootstrap -> $WORK_ROOTFS"
  debootstrap --arch="$ARCH" --variant=minbase "$DEBIAN_SUITE" "$WORK_ROOTFS" "$DEBIAN_MIRROR"
fi

if [[ -n "$INCLUDE_FILE" && -f "$INCLUDE_FILE" ]]; then
  mapfile -t packages < <(grep -v '^#' "$INCLUDE_FILE" | grep -v '^[[:space:]]*$' | sed 's/\r$//' || true)
  if ((${#packages[@]})); then
    chroot "$WORK_ROOTFS" apt-get update
    chroot "$WORK_ROOTFS" apt-get install -y --no-install-recommends "${packages[@]}"
  fi
fi

if [[ "$COG_EXCLUDE_SYSTEMD" == "1" ]]; then
  chroot "$WORK_ROOTFS" apt-get purge -y systemd systemd-sysv 2>/dev/null || true
  chroot "$WORK_ROOTFS" apt-get autoremove -y 2>/dev/null || true
fi

echo "overlay host rootfs files"
rsync -a "$HOST_DIR/rootfs/" "$WORK_ROOTFS/"
chmod +x "$WORK_ROOTFS/etc/rc.sh" "$WORK_ROOTFS/etc/cog/services/"*.sh 2>/dev/null || true

mkdir -p "$WORK_ROOTFS/var/log/cog" "$WORK_ROOTFS/run/cog" "$WORK_ROOTFS/sbin"
echo "$COG_PROFILE" >"$WORK_ROOTFS/etc/cog/profile"
INIT_MODE="${COG_INIT_MODE:-custom}"
echo "$INIT_MODE" >"$WORK_ROOTFS/etc/cog/init_mode"

echo "build gatekeeper /sbin/init"
gcc -O2 -static -o "$WORK_ROOTFS/sbin/init" "$HOST_DIR/src/init.c"

mkdir -p "$WORK_ROOTFS/usr/lib/cogos"
install -m 0755 "$HOST_DIR/scripts/lib/cogos-firstboot-invariants.sh" \
  "$WORK_ROOTFS/usr/lib/cogos/cogos-firstboot-invariants.sh"

if [[ ! -f "$WORK_ROOTFS/run/cog/firstboot.pending" ]]; then
  touch "$WORK_ROOTFS/run/cog/firstboot.pending"
fi

if ! chroot "$WORK_ROOTFS" id -u cogos >/dev/null 2>&1; then
  chroot "$WORK_ROOTFS" useradd -m -s /bin/bash cogos 2>/dev/null || true
fi

if [[ "$SYNC_TO_ARTIFACT" -eq 1 ]]; then
  # 9p/drvfs cannot store symlinks, device nodes, or sockets — do not rsync the tree to /mnt/*.
  echo "publish rootfs staging pointer -> $ROOTFS (tree stays at $WORK_ROOTFS)"
  mkdir -p "$ROOTFS"
  echo "$WORK_ROOTFS" >"$ROOTFS/.cog-rootfs-staging"
  date -u +%Y-%m-%dT%H:%M:%SZ >"$WORK_ROOTFS/.cog-build-stamp"
  cp -f "$WORK_ROOTFS/.cog-build-stamp" "$ROOTFS/.cog-build-stamp"
else
  date -u +%Y-%m-%dT%H:%M:%SZ >"$ROOTFS/.cog-build-stamp"
fi

echo "rootfs ready: $ROOTFS profile=$COG_PROFILE (tree=${WORK_ROOTFS})"
