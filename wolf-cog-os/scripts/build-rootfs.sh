#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  bash wolf-cog-os/scripts/build-rootfs.sh [--profile forge-selfhosted]

Purpose:
  Build a native CoGOS rootfs tree using debootstrap + chroot customization.

Environment:
  COGOS_ROOTFS_OUT            Output rootfs directory
  COGOS_DEBIAN_SUITE          Debian suite (default: trixie)
  COGOS_MIRROR                Debian mirror URL
  COGOS_ARCH                  Target arch (default: amd64)
  COGOS_DAILY_DRIVER_PACKAGES 0|1 install extra daily-driver package profile
  COGOS_ENABLE_PID1           0|1 wire cognitive_init as PID1 (default: 1)
  COGOS_HOSTNAME              Hostname inside rootfs
  COGOS_LOCALE                Locale (default: en_US.UTF-8)
  COGOS_TIMEZONE              Timezone (default: UTC)
  COGOS_DEFAULT_USER          Optional default user (default: operator)
  COGOS_DEFAULT_PASSWORD      Optional password for default user
USAGE
}

CLI_FORGE_PROFILE=""
POSITIONAL_ARGS=()
while (($# > 0)); do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --profile)
      if (($# < 2)); then
        echo "ERROR: --profile requires a value" >&2
        exit 2
      fi
      CLI_FORGE_PROFILE="$2"
      shift 2
      ;;
    --profile=*)
      CLI_FORGE_PROFILE="${1#*=}"
      shift
      ;;
    --)
      shift
      POSITIONAL_ARGS+=("$@")
      break
      ;;
    *)
      POSITIONAL_ARGS+=("$1")
      shift
      ;;
  esac
done

if ((${#POSITIONAL_ARGS[@]} > 0)); then
  echo "ERROR: Unexpected arguments: ${POSITIONAL_ARGS[*]}" >&2
  usage
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"
# shellcheck source=lib/profile-loader.sh
source "$SCRIPT_DIR/lib/profile-loader.sh"
# shellcheck source=lib/stage-forge-layout.sh
source "$SCRIPT_DIR/lib/stage-forge-layout.sh"
# shellcheck source=lib/rootfs-bootstrap.sh
source "$SCRIPT_DIR/lib/rootfs-bootstrap.sh"
# shellcheck source=lib/rootfs-chroot.sh
source "$SCRIPT_DIR/lib/rootfs-chroot.sh"
# shellcheck source=lib/forge-native-paths.sh
source "$SCRIPT_DIR/lib/forge-native-paths.sh"

forge_apply_native_work_paths "${COGOS_ROOTFS_OUT:-$WOLF_ROOTFS_OUT}"

ROOTFS_OUT="${COGOS_ROOTFS_OUT:-$WOLF_ROOTFS_OUT}"
ROOTFS_WORK="${COGOS_ROOTFS_WORK:-${COGOS_WORK}-rootfs-stage}"
forge_apply_native_work_paths "$ROOTFS_OUT"
ROOTFS_OUT="${COGOS_ROOTFS_OUT:-$ROOTFS_OUT}"
ROOTFS_WORK="${COGOS_ROOTFS_WORK:-$ROOTFS_WORK}"

forge_log_rootfs_filesystem "$ROOTFS_OUT" "ROOTFS_OUT"
forge_log_rootfs_filesystem "$ROOTFS_WORK" "ROOTFS_WORK"
DEBIAN_SUITE="${COGOS_DEBIAN_SUITE:-trixie}"
DEBIAN_MIRROR="${COGOS_MIRROR:-http://deb.debian.org/debian}"
DEBIAN_ARCH="${COGOS_ARCH:-amd64}"
DAILY_DRIVER="${COGOS_DAILY_DRIVER_PACKAGES:-0}"
ENABLE_PID1="${COGOS_ENABLE_PID1:-1}"
COGOS_HOSTNAME="${COGOS_HOSTNAME:-wolf-cog-os}"
COGOS_LOCALE="${COGOS_LOCALE:-en_US.UTF-8}"
COGOS_TIMEZONE="${COGOS_TIMEZONE:-UTC}"
COGOS_DEFAULT_USER="${COGOS_DEFAULT_USER:-operator}"
COGOS_DEFAULT_PASSWORD="${COGOS_DEFAULT_PASSWORD:-}"
PAYLOAD="${COGOS_PAYLOAD:-$WOLF_PAYLOAD}"
BASE_PACKAGES_FILE="${COGOS_BASE_PACKAGES_FILE:-$WOLF_PACKAGE_BASE}"
DAILY_PACKAGES_FILE="${COGOS_DAILY_PACKAGES_FILE:-$WOLF_PACKAGE_DAILY}"
FORGE_PACKAGES_FILE="${COGOS_FORGE_PACKAGES_FILE:-$WOLF_PACKAGE_FORGE}"

forge_selector_present() {
  if [[ -n "$CLI_FORGE_PROFILE" ]]; then
    return 0
  fi
  if [[ -n "${COGOS_FORGE_PROFILE:-}" ]]; then
    return 0
  fi
  if [[ -n "${COGOS_BOOT_PROFILE:-}" && "${COGOS_BOOT_PROFILE}" == forge* ]]; then
    return 0
  fi
  return 1
}

forge_emit_rootfs_metadata() {
  local profile_root="$REPO_ROOT/wolf-cog-os/profiles/forge"
  local artifacts_dir="${COGOS_CI_ARTIFACT_DIR:-$REPO_ROOT/ci-artifacts}"
  local validation_mode="${COGOS_FORGE_VALIDATION_MODE:-warn}"
  local resolution_file="$artifacts_dir/profile-resolution.json"
  local validation_file="$artifacts_dir/profile-validation.json"
  local attestation_file="$artifacts_dir/profile-attestation.json"
  local resolution_json
  local resolved_profile
  local resolved_source

  resolution_json="$(forge_emit_resolution_json "$CLI_FORGE_PROFILE" "$profile_root")"
  mkdir -p "$artifacts_dir"
  printf '%s\n' "$resolution_json" >"$resolution_file"

  read -r resolved_profile resolved_source < <(
    python3 - "$resolution_file" <<'PY'
import json
import sys

resolution_path = sys.argv[1]
data = json.load(open(resolution_path, encoding="utf-8"))
print(data.get("profile_id", ""), data.get("source", ""))
PY
  )

  export COGOS_FORGE_PROFILE="$resolved_profile"
  echo "[forge] resolved profile=${resolved_profile} source=${resolved_source}"

  python3 "$SCRIPT_DIR/validate-profile.py" \
    --profile "$resolved_profile" \
    --profiles-root "$profile_root" \
    --mode "$validation_mode" \
    --output "$validation_file"

  python3 "$SCRIPT_DIR/emit-profile-attestation.py" \
    --profile "$resolved_profile" \
    --profiles-root "$profile_root" \
    --validation "$validation_file" \
    --resolution "$resolution_file" \
    --source "build-rootfs.sh" \
    --output "$attestation_file"
}

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "ERROR: build-rootfs.sh must run as root (sudo)." >&2
  exit 2
fi

for tool in debootstrap chroot rsync mount umount awk sed cp ln rm python3; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "Missing required tool: $tool" >&2
    exit 2
  }
done

if forge_selector_present; then
  forge_emit_rootfs_metadata
fi

if [[ ! -d "$PAYLOAD" ]]; then
  echo "ERROR: CoGOS payload not found: $PAYLOAD" >&2
  exit 3
fi

is_inject_rootfs_backend() {
  case "${COGOS_ROOTFS_BACKEND:-debootstrap}" in
    winpe-backend|darwin-backend|android-backend) return 0 ;;
    *) return 1 ;;
  esac
}

if is_inject_rootfs_backend; then
  :
else
if [[ ! -f "$BASE_PACKAGES_FILE" ]]; then
  echo "ERROR: Base package profile not found: $BASE_PACKAGES_FILE" >&2
  exit 3
fi
fi

if [[ "$DAILY_DRIVER" == "1" && ! -f "$DAILY_PACKAGES_FILE" ]]; then
  echo "ERROR: Daily-driver package profile not found: $DAILY_PACKAGES_FILE" >&2
  exit 3
fi

mkdir -p "$(dirname "$ROOTFS_OUT")" "$(dirname "$ROOTFS_WORK")"
ROOTFS_OUT="$(readlink -f "$ROOTFS_OUT" 2>/dev/null || echo "$ROOTFS_OUT")"
ROOTFS_WORK="$(readlink -f "$ROOTFS_WORK" 2>/dev/null || echo "$ROOTFS_WORK")"

rootfs_refuse_drvfs() {
  local path="$1"
  local label="$2"
  local parent="${path%/*}"
  [[ -n "$parent" && "$parent" != "$path" ]] || parent="$path"
  local fstype
  fstype="$(df -T "$parent" 2>/dev/null | tail -1 | awk '{print $2}')"
  if [[ "$fstype" == "9p" ]]; then
    echo "ERROR: $label on Windows mount (9p): $path" >&2
    echo "       debootstrap tar/symlink extract fails on DrvFs." >&2
    echo "       Fix: export COGOS_ROOTFS_OUT=\$HOME/.cogos-forge-work/rootfs-forge" >&2
    echo "             export COGOS_WORK=\$HOME/.cogos-forge-work" >&2
    echo "             sudo -E make rootfs-forge" >&2
    exit 4
  fi
}

rootfs_refuse_drvfs "$ROOTFS_OUT" "COGOS_ROOTFS_OUT"
rootfs_refuse_drvfs "$ROOTFS_WORK" "COGOS_ROOTFS_WORK"

mkdir -p "$ROOTFS_WORK"
rm -rf "$ROOTFS_OUT"

MOUNTED=0
cleanup() {
  if (( MOUNTED == 1 )); then
    umount -lf "$ROOTFS_OUT/dev/pts" 2>/dev/null || true
    umount -lf "$ROOTFS_OUT/dev" 2>/dev/null || true
    umount -lf "$ROOTFS_OUT/proc" 2>/dev/null || true
    umount -lf "$ROOTFS_OUT/sys" 2>/dev/null || true
  fi
  rm -f "$ROOTFS_OUT/tmp/cogos-chroot-setup.sh" "$ROOTFS_OUT/tmp/cogos-packages.txt"
}
trap cleanup EXIT

echo "[1/7] Bootstrap rootfs (backend=${COGOS_ROOTFS_BACKEND:-debootstrap})"
rootfs_bootstrap "$ROOTFS_OUT"

echo "[2/7] Prepare chroot mounts and package list"
mkdir -p "$ROOTFS_OUT/dev/pts" "$ROOTFS_OUT/proc" "$ROOTFS_OUT/sys" "$ROOTFS_OUT/tmp"

if is_inject_rootfs_backend; then
  echo "[3/7] Inject backend customization (backend=${COGOS_ROOTFS_BACKEND})"
  rootfs_chroot_customize "$ROOTFS_OUT"
else
mount --bind /dev "$ROOTFS_OUT/dev"
mount --bind /dev/pts "$ROOTFS_OUT/dev/pts"
mount -t proc proc "$ROOTFS_OUT/proc"
mount -t sysfs sys "$ROOTFS_OUT/sys"
MOUNTED=1

cp /etc/resolv.conf "$ROOTFS_OUT/etc/resolv.conf"

awk '{ sub(/\r$/, ""); if (NF && $1 !~ /^#/) print }' "$BASE_PACKAGES_FILE" >"$ROOTFS_OUT/tmp/cogos-packages.txt"
if [[ "$DAILY_DRIVER" == "1" ]]; then
  awk '{ sub(/\r$/, ""); if (NF && $1 !~ /^#/) print }' "$DAILY_PACKAGES_FILE" >>"$ROOTFS_OUT/tmp/cogos-packages.txt"
fi
if forge_selector_present; then
  if [[ ! -f "$FORGE_PACKAGES_FILE" ]]; then
    echo "ERROR: Forge package profile not found: $FORGE_PACKAGES_FILE" >&2
    exit 3
  fi
  awk '{ sub(/\r$/, ""); if (NF && $1 !~ /^#/) print }' "$FORGE_PACKAGES_FILE" >>"$ROOTFS_OUT/tmp/cogos-packages.txt"
fi

if [[ "${COGOS_ROOTFS_BACKEND:-debootstrap}" == "pacstrap" && -f "$WOLF_PACKAGE_CONFIG/arch-base.txt" ]]; then
  cp "$WOLF_PACKAGE_CONFIG/arch-base.txt" "$ROOTFS_OUT/tmp/cogos-packages.txt"
fi

echo "[3/7] Chroot install and base system configuration (backend=${COGOS_ROOTFS_BACKEND:-debootstrap})"
rootfs_chroot_customize "$ROOTFS_OUT"
fi

echo "[4/7] Inject CoGOS runtime payload"
rsync -aH \
  --exclude 'opt/cogos/memory/***' \
  --exclude '**/__pycache__/***' \
  --exclude '*.pyc' \
  "$PAYLOAD/" "$ROOTFS_OUT/"

mkdir -p \
  "$ROOTFS_OUT/opt/cogos/memory/backups" \
  "$ROOTFS_OUT/opt/cogos/memory/creative" \
  "$ROOTFS_OUT/opt/cogos/memory/logs" \
  "$ROOTFS_OUT/opt/cogos/memory/traces" \
  "$ROOTFS_OUT/opt/cogos/memory/tmp"

chmod_if_exists() {
  local p
  for p in "$@"; do
    if [[ -e "$p" ]]; then
      chmod +x "$p"
    fi
  done
  return 0
}

chmod_if_exists \
  "$ROOTFS_OUT/opt/cogos/bin/cognitive_init" \
  "$ROOTFS_OUT/opt/cogos/bin/cogos_boot.py" \
  "$ROOTFS_OUT/opt/cogos/bin/cogos_daemon.py" \
  "$ROOTFS_OUT/usr/lib/cogos/firstboot.sh" \
  "$ROOTFS_OUT/usr/local/bin/cogos-install" \
  "$ROOTFS_OUT/usr/local/bin/cogos-install-finish" \
  "$ROOTFS_OUT/usr/local/bin/cogos-first-boot" \
  "$ROOTFS_OUT/usr/local/bin/cogos-persist" \
  "$ROOTFS_OUT/usr/local/bin/cogos-first-run"

echo "[5/7] Wire CoGOS PID1 policy"
if [[ "$ENABLE_PID1" == "1" ]]; then
  native_init=""
  for candidate in "$ROOTFS_OUT/usr/sbin/init" "$ROOTFS_OUT/sbin/init"; do
    if [[ -L "$candidate" || -f "$candidate" ]]; then
      native_init="$(readlink -f "$candidate" 2>/dev/null || echo "$candidate")"
      break
    fi
  done
  if [[ -z "$native_init" || ! -e "$native_init" ]]; then
    echo "ERROR: native init not found in rootfs." >&2
    exit 5
  fi
  if [[ ! -e "$ROOTFS_OUT/usr/sbin/init.original" ]]; then
    cp -a "$native_init" "$ROOTFS_OUT/usr/sbin/init.original"
    chmod +x "$ROOTFS_OUT/usr/sbin/init.original" || true
  fi
  rm -f "$ROOTFS_OUT/usr/sbin/init"
  ln -s /opt/cogos/bin/cognitive_init "$ROOTFS_OUT/usr/sbin/init"
  if [[ -d "$ROOTFS_OUT/sbin" ]]; then
    rm -f "$ROOTFS_OUT/sbin/init"
    ln -s /opt/cogos/bin/cognitive_init "$ROOTFS_OUT/sbin/init"
  fi
else
  if [[ -f "$ROOTFS_OUT/usr/sbin/init.original" ]]; then
    rm -f "$ROOTFS_OUT/usr/sbin/init"
    ln -s /usr/sbin/init.original "$ROOTFS_OUT/usr/sbin/init"
    if [[ -d "$ROOTFS_OUT/sbin" ]]; then
      rm -f "$ROOTFS_OUT/sbin/init"
      ln -s /usr/sbin/init.original "$ROOTFS_OUT/sbin/init"
    fi
  fi
fi

echo "[6/7] Final cleanup and compaction"
rm -rf "$ROOTFS_OUT/tmp/"*
rm -rf "$ROOTFS_OUT/var/tmp/"*
find "$ROOTFS_OUT/var/log" -type f -name '*.log' -delete 2>/dev/null || true

echo "[7/7] Rootfs ready"
FORGE_ACTIVE=0
if forge_selector_present; then
  FORGE_ACTIVE=1
  echo "[forge] staging cockpit layout"
  stage_forge_layout "$ROOTFS_OUT"
fi
echo "Built CoGOS rootfs at: $ROOTFS_OUT"
echo "Profile: daily-driver=$DAILY_DRIVER pid1=$ENABLE_PID1 suite=$DEBIAN_SUITE arch=$DEBIAN_ARCH forge=$FORGE_ACTIVE"
