#!/usr/bin/env bash
set -euo pipefail

# Step markers on stderr so sudo/non-tty runs stay visible (stdout may block-buffer).
forge_log_step() {
  printf '%s\n' "$*" >&2
}

on_build_error() {
  forge_log_step "ERROR: build failed at line ${BASH_LINENO[0]:-?} (exit ${2:-$?})"
}
trap on_build_error ERR

usage() {
  cat <<'USAGE'
Usage:
  bash wolf-cog-os/scripts/build.sh [--profile forge-selfhosted] [/path/to/debian-live-13.5.0-amd64-cinnamon.iso]

Output:
  wolf-cog-os/output/wolf-cog-os-<tag>.iso  (or COGOS_OUT)

Environment:
  COGOS_BUILD_FROM_TREE=1 Use prebuilt rootfs tree as source
  COGOS_ROOTFS_SRC       Rootfs source directory for tree mode
  COGOS_BUILD_ROOTFS_FIRST=1 Build rootfs first using build-rootfs.sh
  COGOS_PAYLOAD       Pre-cached payload dir (recommended on WSL ext4)
  COGOS_ENABLE_PID1=0 Required for live-safe ISO (disk takeover still via cogos-install-finish)
  COGOS_STEALTH_INSTALL=1 Keep stock Debian branding on live ISO
  COGOS_GRUB_MERGE=1  Patch GRUB (metal/surprise/forge profile)
  COGOS_BOOT_PROFILE=surprise|metal|debian|forge|normal
  COGOS_GRAPHICAL_INSTALL=1  Debian-style Start installer (Calamares + cogos-install-finish)
  COGOS_SQUASHFS_COMP=xz|gzip
  COGOS_PLYMOUTH_POLICY=required|optional|forbidden  (live-boot integrity gate)
  COGOS_SKIP_BOOT_VALIDATION=1  Debug only; bypasses pre-pack live-safe gate
  COGOS_PACK_ONLY=1             Skip squashfs rebuild; pack ISO from existing workdir
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

if ((${#POSITIONAL_ARGS[@]} > 1)); then
  echo "ERROR: Unexpected arguments: ${POSITIONAL_ARGS[*]}" >&2
  usage
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"
# shellcheck source=lib/profile-loader.sh
source "$SCRIPT_DIR/lib/profile-loader.sh"
# shellcheck source=patch_grub_merge.sh
source "$SCRIPT_DIR/patch_grub_merge.sh"
# shellcheck source=patch_calamares_surprise.sh
source "$SCRIPT_DIR/patch_calamares_surprise.sh"
# shellcheck source=patch-debian-install-media.sh
source "$SCRIPT_DIR/patch-debian-install-media.sh"
# shellcheck source=stage-di-iso-payload.sh
source "$SCRIPT_DIR/stage-di-iso-payload.sh"
# shellcheck source=embed-cogos-in-di-initrd.sh
source "$SCRIPT_DIR/embed-cogos-in-di-initrd.sh"
# shellcheck source=patch-live-session.sh
source "$SCRIPT_DIR/patch-live-session.sh"
# shellcheck source=build_iso.sh
source "$SCRIPT_DIR/build_iso.sh"
# shellcheck source=lib/replay-adapters.sh
source "$SCRIPT_DIR/lib/replay-adapters.sh"
# shellcheck source=lib/live-systemd-init.sh
source "$SCRIPT_DIR/lib/live-systemd-init.sh"
# shellcheck source=lib/stage-forge-layout.sh
source "$SCRIPT_DIR/lib/stage-forge-layout.sh"

ISO="${POSITIONAL_ARGS[0]:-$DEBIAN_BASE_ISO}"
WORK="${COGOS_WORK:-/tmp/wolf-cog-os-build-${COGOS_TAG//[^A-Za-z0-9]/-}}"
OUT="$(wolf_iso_out)"
PAYLOAD="${COGOS_PAYLOAD:-$WOLF_PAYLOAD}"
ROOTFS_SRC="${COGOS_ROOTFS_SRC:-$WOLF_ROOTFS_OUT}"
BUILD_FROM_TREE="${COGOS_BUILD_FROM_TREE:-0}"
SQUASHFS_COMP="${COGOS_SQUASHFS_COMP:-xz}"
SQUASHFS_BLOCK="${COGOS_SQUASHFS_BLOCK:-1M}"
REPLAY_ISO="$ISO"

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

forge_emit_build_metadata() {
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
    --source "build.sh" \
    --output "$attestation_file"
}

forge_emit_final_attestation() {
  local profile_root="$REPO_ROOT/wolf-cog-os/profiles/forge"
  local artifacts_dir="${COGOS_CI_ARTIFACT_DIR:-$REPO_ROOT/ci-artifacts}"
  local validation_file="$artifacts_dir/profile-validation.json"
  local resolution_file="$artifacts_dir/profile-resolution.json"
  local attestation_file="$artifacts_dir/profile-attestation.json"
  local manifest_path="${COGOS_ARTIFACT_MANIFEST:-$artifacts_dir/artifact-manifest.json}"

  if [[ ! -f "$manifest_path" ]]; then
    manifest_path=""
  fi

  python3 "$SCRIPT_DIR/emit-profile-attestation.py" \
    --profile "${COGOS_FORGE_PROFILE:-forge-selfhosted}" \
    --profiles-root "$profile_root" \
    --validation "$validation_file" \
    --resolution "$resolution_file" \
    --source "build.sh" \
    --output "$attestation_file" \
    --iso-path "$OUT" \
    --manifest-path "$manifest_path"
}

chmod_existing() {
  local f
  for f in "$@"; do
    [[ -e "$f" ]] || continue
    if ! chmod +x "$f" 2>/dev/null; then
      forge_log_step "WARN: chmod +x skipped: $f"
    fi
  done
}

normalize_systemd_unit_modes() {
  local root="${1:-}"
  find "$root/etc/systemd/system" \( -name '*.service' -o -name '*.conf' \) -type f \
    -exec chmod 644 {} + 2>/dev/null || true
}

write_live_install_guide() {
  local mode="${1:-metal}"
  local live_label="Wolf CoG OS — Live (recommended)"
  if [[ "${COGOS_FULL_RUNTIME:-0}" == "1" ]]; then
    live_label="Wolf CoG OS — Live (full runtime, recommended)"
  fi
  mkdir -p "$WORK/rootfs/usr/share/cogos"
  cat > "$WORK/rootfs/usr/share/cogos/INSTALL_FROM_LIVE.txt" <<TXT
Wolf CoG OS — install from live session
======================================

1. Boot "$live_label".
2. Open a root terminal.
3. List disks:  lsblk
4. Plan (no writes):  cogos-install plan --target /dev/nvme0n1
5. Install (DESTROYS target disk):

   cogos-install apply --target /dev/nvme0n1 --yes --confirm-erase nvme0n1 \
     --hostname wolf-cog-os --user operator

6. Reboot, remove USB, boot internal disk.
7. First boot enables the full CoGOS runtime (Nova / daily driver stack).

Logs: /opt/cogos/memory/logs/install.log
Proof: cogos-install proof
TXT

  if [[ "$mode" == "debian" || "${COGOS_GRAPHICAL_INSTALL:-0}" == "1" ]]; then
    cat >> "$WORK/rootfs/usr/share/cogos/INSTALL_FROM_LIVE.txt" <<'TXT'

Graphical install (Debian gtk installer — recommended)
----------------------------------------------------
1. At GRUB, choose **Start Wolf CoG OS installer** (stock Debian gtk d-i).
2. Use the graphical installer (partition, user, etc.) as normal.
3. When install completes, Wolf CoG OS late_command deploys full runtime to disk.
4. Reboot, remove USB, boot internal disk — first boot enables Nova/daily driver.

Also available under **Wolf CoG OS advanced install** (expert/text/rescue modes).

Live session (try without installing)
-------------------------------------
Boot **Wolf CoG OS — Live (full runtime)**. Terminal install: \`sudo cogos-install apply\`.

Do NOT use unpatched stock Debian d-i without the Wolf preseed hook.
TXT
  fi

  if [[ "$mode" == "forge" ]]; then
    cat > "$WORK/rootfs/usr/share/cogos/FORGE_MODE.txt" <<'TXT'
Wolf CoG OS — Forge Mode
========================

Boot "Enter Forge Mode" from the GRUB menu, then run:

  forge-menu

Pipeline specs live under /forge/pipelines/.
Built ISOs and logs are written to /forge/output/.
TXT
  fi
}

detect_calamares_assets() {
  local grub_start="$WORK/iso/boot/grub/install_start.cfg"
  local grub_cfg="$WORK/iso/boot/grub/install.cfg"
  local settings="$WORK/rootfs/etc/calamares/settings.conf"
  local reason=()

  COGOS_CALAMARES_AVAILABLE=1
  if [[ ! -f "$grub_start" ]]; then
    COGOS_CALAMARES_AVAILABLE=0
    reason+=("missing boot/grub/install_start.cfg")
  fi
  if [[ ! -f "$grub_cfg" ]]; then
    COGOS_CALAMARES_AVAILABLE=0
    reason+=("missing boot/grub/install.cfg")
  fi
  if [[ ! -f "$settings" ]]; then
    COGOS_CALAMARES_AVAILABLE=0
    reason+=("missing rootfs etc/calamares/settings.conf")
  fi

  export COGOS_CALAMARES_AVAILABLE
  if [[ "$COGOS_CALAMARES_AVAILABLE" == "1" ]]; then
    echo "[preflight] Calamares assets found: surprise installer submenu enabled"
  else
    echo "[preflight] WARN: Calamares assets incomplete: ${reason[*]}" >&2
    echo "[preflight] WARN: Universal ISO will keep metal install path and provide live fallback guidance" >&2
  fi
}

validate_tree_rootfs() {
  local rootfs_dir="$1"
  [[ -d "$rootfs_dir" ]] || return 1
  [[ -f "$rootfs_dir/etc/os-release" ]] || return 1
  [[ -d "$rootfs_dir/opt/cogos" ]] || return 1
  return 0
}

restore_native_init() {
  restore_live_systemd_init_links "$WORK/rootfs" || {
    echo "ERROR: unable to pin live init to systemd" >&2
    exit 5
  }
}

verify_live_systemd_init() {
  verify_live_systemd_init_links "$WORK/rootfs" || {
    echo "ERROR: live init must resolve to systemd binary (merged-usr aware)" >&2
    exit 5
  }
}

run_live_boot_integrity_gate() {
  local proof_dir="${COGOS_BUILD_PROOF_DIR:-$WORK/proof/live-boot-integrity}"
  local plymouth_policy="${COGOS_PLYMOUTH_POLICY:-optional}"
  local validator="$SCRIPT_DIR/validate-live-boot-integrity.sh"

  if [[ "${COGOS_REPLAY_ADAPTER:-}" == "fedora-liveos-layout" ]]; then
    forge_log_step "[7/9] Skipping Debian live-boot gate for fedora-family substrate replay"
    return 0
  fi

  if [[ "${COGOS_SKIP_BOOT_VALIDATION:-0}" == "1" ]]; then
    echo "WARN: live-boot integrity gate skipped (COGOS_SKIP_BOOT_VALIDATION=1)" >&2
    return 0
  fi

  [[ -x "$validator" || -f "$validator" ]] || {
    echo "ERROR: live-boot integrity validator missing: $validator" >&2
    exit 5
  }

  echo "[7/9] Pre-pack live-boot integrity gate (live-safe contract must pass before ISO emit)"
  bash "$validator" \
    --rootfs "$WORK/rootfs" \
    --iso-tree "$WORK/iso" \
    --proof-dir "$proof_dir" \
    --plymouth-policy "$plymouth_policy"
  echo "Live-safe contract proven: $proof_dir"
}

enable_cogos_init() {
  local native_init_real=""
  local candidate
  for candidate in \
    "$WORK/rootfs/usr/sbin/init" \
    "$WORK/rootfs/sbin/init"; do
    if [[ -L "$candidate" || -f "$candidate" ]]; then
      native_init_real="$(readlink -f "$candidate" 2>/dev/null || echo "$candidate")"
      break
    fi
  done

  if [[ -z "$native_init_real" || ! -e "$native_init_real" ]]; then
    if [[ -f "$WORK/rootfs/usr/sbin/init.original" ]]; then
      native_init_real="$WORK/rootfs/usr/sbin/init.original"
    else
      echo "Native init not found at /usr/sbin/init or /sbin/init." >&2
      exit 5
    fi
  fi

  if [[ ! -e "$WORK/rootfs/usr/sbin/init.original" ]]; then
    cp -a "$native_init_real" "$WORK/rootfs/usr/sbin/init.original"
  fi
  chmod_existing "$WORK/rootfs/usr/sbin/init.original"
  rm -f "$WORK/rootfs/usr/sbin/init"
  ln -s /opt/cogos/bin/cognitive_init "$WORK/rootfs/usr/sbin/init"
  if [[ -e "$WORK/rootfs/sbin" ]]; then
    rm -f "$WORK/rootfs/sbin/init"
    ln -s /opt/cogos/bin/cognitive_init "$WORK/rootfs/sbin/init"
  fi
}

for tool in unsquashfs mksquashfs xorriso rsync find python3; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "Missing required tool: $tool" >&2
    exit 2
  }
done

if forge_selector_present; then
  forge_emit_build_metadata
  export COGOS_BOOT_PROFILE="${COGOS_BOOT_PROFILE:-forge}"
  export COGOS_GRUB_MERGE="${COGOS_GRUB_MERGE:-1}"
  export COGOS_ENABLE_PID1="${COGOS_ENABLE_PID1:-0}"
  export COGOS_METAL_INSTALL="${COGOS_METAL_INSTALL:-1}"
  export COGOS_LIVE_FINDISO="${COGOS_LIVE_FINDISO:-0}"
fi

if [[ ! -f "$ISO" ]]; then
  echo "ISO not found: $ISO" >&2
  exit 3
fi

if [[ "${COGOS_BUILD_ROOTFS_FIRST:-0}" == "1" ]]; then
  echo "[preflight] Build rootfs tree first"
  bash "$SCRIPT_DIR/build-rootfs.sh"
fi

if [[ "$BUILD_FROM_TREE" == "1" ]]; then
  if [[ ! -d "$ROOTFS_SRC" ]]; then
    echo "Rootfs source not found: $ROOTFS_SRC" >&2
    exit 3
  fi
  ROOTFS_SRC="$(readlink -f "$ROOTFS_SRC" 2>/dev/null || echo "$ROOTFS_SRC")"
  if ! validate_tree_rootfs "$ROOTFS_SRC"; then
    echo "Invalid rootfs tree: $ROOTFS_SRC" >&2
    echo "Expected at least: etc/os-release and opt/cogos/" >&2
    exit 3
  fi
else
  if [[ ! -d "$PAYLOAD" ]]; then
    echo "CoGOS payload not found: $PAYLOAD" >&2
    exit 3
  fi
fi

ISO="$(readlink -f "$ISO")"
replay_adapter_detect "$ISO"
echo "Replay adapter: ${COGOS_REPLAY_ADAPTER:-debian-live-layout}"

resolve_sfs_source() {
  replay_resolve_sfs "$WORK/iso"
}

workdir_resume_ready() {
  replay_workdir_ready "$WORK"
}

extract_rootfs_from_substrate() {
  if [[ "$BUILD_FROM_TREE" == "1" ]]; then
    if [[ ! -d "$ROOTFS_SRC" ]]; then
      echo "ERROR: rootfs tree missing: $ROOTFS_SRC" >&2
      echo "       Build it first: sudo -E bash wolf-cog-os/scripts/build-rootfs.sh --profile forge-selfhosted" >&2
      exit 3
    fi
    echo "[3/9] Stage root filesystem from tree: $ROOTFS_SRC"
    rsync -aH --delete "$ROOTFS_SRC/" "$WORK/rootfs/"
  else
    echo "[3/9] Extract root filesystem: ${SFS_NAME:-squashfs} (adapter=${COGOS_REPLAY_ADAPTER:-debian-live-layout})"
    replay_extract_rootfs "$WORK/iso" "$WORK/rootfs"
  fi
}

refresh_build_workdir() {
  mkdir -p "$WOLF_OUTPUT"
  if [[ "$BUILD_FROM_TREE" == "1" && "$ROOTFS_SRC" == "$WORK/"* ]]; then
    echo "[work] Refresh ISO staging under $WORK (keeping rootfs tree at $ROOTFS_SRC)"
    rm -rf "$WORK/iso" "$WORK/rootfs"
    mkdir -p "$WORK/iso" "$WORK/rootfs"
    return 0
  fi
  rm -rf "$WORK"
  mkdir -p "$WORK/iso" "$WORK/rootfs" "$WOLF_OUTPUT"
}

if [[ "${COGOS_RESUME_WORK:-0}" == "1" ]] && workdir_resume_ready; then
  echo "[resume] Reusing workdir $WORK (skip ISO extract + unsquashfs; re-merge payload and finish)"
  mkdir -p "$WORK/rootfs" "$WOLF_OUTPUT"
  echo "[2/9] Locate substrate root image (resume, adapter=${COGOS_REPLAY_ADAPTER:-debian-live-layout})"
  resolve_sfs_source
  [[ -n "$SFS_SOURCE" ]] || {
    echo "No root image found inside resumed workdir." >&2
    exit 4
  }
  echo "Using root filesystem image: $SFS_SOURCE"
elif [[ "${COGOS_RESUME_WORK:-0}" == "1" ]]; then
  echo "WARN: COGOS_RESUME_WORK=1 but workdir incomplete; running full rebuild" >&2
  refresh_build_workdir
  echo "[1/9] Extract ISO contents"
  xorriso -osirrox on -indev "$ISO" -extract / "$WORK/iso" >/dev/null
  chmod -R u+w "$WORK/iso"
  echo "[2/9] Locate substrate root image (adapter=${COGOS_REPLAY_ADAPTER:-debian-live-layout})"
  resolve_sfs_source
  [[ -n "$SFS_SOURCE" ]] || {
    echo "No root image found inside ISO." >&2
    exit 4
  }
  echo "Using root filesystem image: $SFS_SOURCE"
  extract_rootfs_from_substrate
else
  refresh_build_workdir

  echo "[1/9] Extract ISO contents"
  xorriso -osirrox on -indev "$ISO" -extract / "$WORK/iso" >/dev/null
  chmod -R u+w "$WORK/iso"

  echo "[2/9] Locate substrate root image (adapter=${COGOS_REPLAY_ADAPTER:-debian-live-layout})"
  resolve_sfs_source
  if [[ -z "$SFS_SOURCE" ]]; then
    echo "No root image found inside ISO." >&2
    exit 4
  fi
  echo "Using root filesystem image: $SFS_SOURCE"
  extract_rootfs_from_substrate
fi

if [[ "$BUILD_FROM_TREE" == "1" ]]; then
  echo "[4/9] Tree mode active: skipping payload overlay merge"
else
  echo "[4/9] Stage Wolf CoG OS CoGOS payload"
  PAYLOAD_SRC="$PAYLOAD"
  if [[ "$PAYLOAD" == /mnt/* ]]; then
    PAYLOAD_CACHE="${COGOS_PAYLOAD_CACHE:-${HOME}/.cogos-payload-cache}"
    echo "[4a/9] Mirror payload from Windows drive to WSL ext4 (NOT frozen — often 5-20 min)"
    mkdir -p "$PAYLOAD_CACHE"
    if rsync -a --delete --info=progress2 \
      --exclude 'opt/cogos/memory/' \
      --exclude '**/__pycache__/' \
      --exclude '*.pyc' \
      "$PAYLOAD/" "$PAYLOAD_CACHE/"; then
      PAYLOAD_SRC="$PAYLOAD_CACHE"
      echo "[4a/9] Payload cache ready"
    else
      echo "WARN: payload cache rsync had warnings; using drvfs payload directly" >&2
      PAYLOAD_SRC="$PAYLOAD"
    fi
  else
    echo "[4a/9] Using payload on native filesystem: $PAYLOAD"
  fi
  echo "[4b/9] Merge payload into rootfs (please wait)..."
  rsync -aH --info=progress2 \
    --exclude 'opt/cogos/memory/***' \
    --exclude '**/__pycache__/***' \
    --exclude '*.pyc' \
    "$PAYLOAD_SRC/" "$WORK/rootfs/" || rsync_rc=$?
  rsync_rc="${rsync_rc:-0}"
  if (( rsync_rc != 0 && rsync_rc != 23 && rsync_rc != 24 )); then
    echo "ERROR: payload rsync failed (exit $rsync_rc)" >&2
    exit 1
  fi
  echo "[4c/9] Payload merged into rootfs"
  rm -f "$WORK/rootfs/etc/init.d/90cogos" 2>/dev/null || true
  # shellcheck source=lib/normalize-boot-stack-lf.sh
  source "$SCRIPT_DIR/lib/normalize-boot-stack-lf.sh"
  normalize_boot_stack_lf "$WORK/rootfs"
  verify_boot_stack_lf "$WORK/rootfs" || {
    echo "ERROR: boot stack launchers still contain CRLF after normalize" >&2
    exit 1
  }
fi

echo "[4c+] Runtime prep: memory dirs, file modes, install hooks"
mkdir -p \
  "$WORK/rootfs/opt/cogos/memory/backups" \
  "$WORK/rootfs/opt/cogos/memory/creative" \
  "$WORK/rootfs/opt/cogos/memory/logs" \
  "$WORK/rootfs/opt/cogos/memory/traces" \
  "$WORK/rootfs/opt/cogos/memory/tmp"
forge_log_step "[4c+] Memory dirs ready"

forge_log_step "[4c+] Setting CoGOS binary modes"
chmod_existing \
  "$WORK/rootfs/opt/cogos/bin/cognitive_init" \
  "$WORK/rootfs/opt/cogos/bin/cogos_shell" \
  "$WORK/rootfs/opt/cogos/bin/cogos_boot.py" \
  "$WORK/rootfs/opt/cogos/bin/cogos_daemon.py" \
  "$WORK/rootfs/opt/cogos/bin/cogos_first_run.py" \
  "$WORK/rootfs/opt/cogos/bin/cogos_supernova.py" \
  "$WORK/rootfs/opt/cogos/bin/cogos_daily_driver.py" \
  "$WORK/rootfs/opt/cogos/bin/cogos_manifest.py" \
  "$WORK/rootfs/opt/cogos/bin/cogos_install_proof.py" \
  "$WORK/rootfs/opt/cogos/bin/cogos_master_boot.py"
forge_log_step "[4c+] Binary modes done"

if forge_selector_present; then
  if [[ "$BUILD_FROM_TREE" == "1" && -f "$WORK/rootfs/forge/scripts/build/build.sh" ]]; then
    forge_log_step "[4e/9] Forge cockpit already in rootfs tree; skipping re-stage"
  else
    forge_log_step "[4e/9] Stage Forge cockpit layout"
    stage_forge_layout "$WORK/rootfs"
  fi
fi

if [[ "${COGOS_STEALTH_INSTALL:-0}" == "1" ]]; then
  forge_log_step "[4d/9] Stealth install: keeping stock Debian identity on live ISO"
else
  forge_log_step "[4d/9] Branding live session"
  patch_live_wolf_branding "$WORK/rootfs"
  if [[ "${COGOS_BOOT_PROFILE:-}" == "debian" || "${COGOS_DI_INSTALL:-0}" == "1" ]]; then
    install_di_live_desktop "$WORK/rootfs"
  fi
fi

if [[ "${COGOS_BOOT_PROFILE:-}" == "debian" || "${COGOS_DI_INSTALL:-0}" == "1" ]]; then
  echo "[4d/9] Stage Debian installer payload on ISO (/install/wolf-cog-os)"
  stage_di_iso_payload "$WORK/rootfs"
  echo "[4e/9] Embed CoGOS runtime + preseed into gtk/text d-i initrd"
  embed_cogos_in_di_initrd "$WORK/iso/install/wolf-cog-os/runtime.tar"
  echo "[4e+/9] Verify gtk d-i initrd WiFi stack"
  bash "$SCRIPT_DIR/verify-di-initrd-wifi.sh"
fi

if [[ "${COGOS_SURPRISE_INSTALL:-0}" == "1" || "${COGOS_GRAPHICAL_INSTALL:-0}" == "1" ]]; then
  patch_calamares_surprise "$WORK/rootfs"
  install_calamares_live_autostart "$WORK/rootfs"
fi

if [[ "${COGOS_BOOT_PROFILE:-}" == "metal" ]]; then
  write_live_install_guide metal
elif [[ "${COGOS_BOOT_PROFILE:-}" == "debian" ]]; then
  write_live_install_guide debian
elif [[ "${COGOS_BOOT_PROFILE:-}" == "forge" ]]; then
  write_live_install_guide forge
fi

if [[ "${COGOS_BOOT_PROFILE:-}" == "debian" || "${COGOS_GRAPHICAL_INSTALL:-0}" == "1" ]]; then
  detect_calamares_assets
fi

if [[ "${COGOS_GRUB_MERGE:-0}" == "1" ]]; then
  forge_log_step "[4f/9] Patch GRUB boot menu"
  case "${COGOS_BOOT_PROFILE:-}" in
    surprise)
      patch_grub_surprise
      ;;
    metal)
      patch_grub_metal_installer
      ;;
    debian)
      patch_grub_debian_installer
      ;;
    forge)
      patch_grub_forge
      ;;
    *)
      patch_grub_merge
      ;;
  esac
fi

if [[ -f "$WORK/rootfs/opt/cogos/bin/cogos_manifest.py" && -f "$WORK/rootfs/opt/cogos/config/release_manifest.json" && "$BUILD_FROM_TREE" != "1" ]]; then
  forge_log_step "[4g/9] Signing release manifest (optional)"
  timeout 60 env COGOS_ROOT="$WORK/rootfs/opt/cogos" python3 "$WORK/rootfs/opt/cogos/bin/cogos_manifest.py" sign \
    "$WORK/rootfs/opt/cogos/config/release_manifest.json" 2>/dev/null || true
fi

forge_log_step "[5/9] Install CoGOS operator layer"
chmod_existing \
  "$WORK/rootfs/usr/lib/cogos/firstboot.sh" \
  "$WORK/rootfs/usr/lib/cogos/governance-grace.sh" \
  "$WORK/rootfs/usr/lib/cogos/governance-daemon" \
  "$WORK/rootfs/usr/lib/cogos/spine" \
  "$WORK/rootfs/usr/lib/cogos/observer" \
  "$WORK/rootfs/usr/local/bin/cogos-install" \
  "$WORK/rootfs/usr/local/bin/cogos-install-finish" \
  "$WORK/rootfs/usr/local/bin/cogos-launch-installer" \
  "$WORK/rootfs/usr/local/bin/cogos-launch-di-installer" \
  "$WORK/rootfs/usr/local/bin/cogos-live-welcome" \
  "$WORK/rootfs/usr/local/bin/cogos-reveal-identity" \
  "$WORK/rootfs/usr/local/bin/cogos-first-boot" \
  "$WORK/rootfs/usr/local/bin/cogos-persist" \
  "$WORK/rootfs/usr/local/bin/cogos-status" \
  "$WORK/rootfs/usr/local/bin/cogos-shell" \
  "$WORK/rootfs/usr/local/bin/cogos-doctor" \
  "$WORK/rootfs/usr/local/bin/cogos-first-run" \
  "$WORK/rootfs/usr/local/bin/cogos-supernova" \
  "$WORK/rootfs/usr/local/bin/cogos-daily-driver" \
  "$WORK/rootfs/usr/local/bin/cogos-runtime-start" \
  "$WORK/rootfs/usr/local/bin/cogos-runtime-stop" \
  "$WORK/rootfs/usr/local/bin/cogos-master-boot" \
  "$WORK/rootfs/usr/local/bin/cogos-recovery"

normalize_systemd_unit_modes "$WORK/rootfs"
forge_log_step "[5/9] Operator layer ready"

forge_log_step "[6/9] Enforce live-safe PID1 invariants"
if [[ "${COGOS_ENABLE_PID1:-0}" != "0" ]]; then
  echo "ERROR: live-safe build forbids runtime PID1 takeover (set COGOS_ENABLE_PID1=0)." >&2
  echo "ERROR: keep install-on-disk takeover via cogos-install-finish." >&2
  exit 5
fi
restore_native_init
verify_live_systemd_init
echo "Live PID1 pinned to systemd; disk takeover remains in cogos-install-finish"

run_live_boot_integrity_gate

if [[ "${COGOS_PACK_ONLY:-0}" == "1" ]]; then
  forge_log_step "[8/9] SKIP squashfs rebuild (COGOS_PACK_ONLY=1)"
  resolve_sfs_source
  SFS_SOURCE="$(replay_sfs_write_path "$WORK/iso")"
  [[ -f "${SFS_SOURCE:-}" ]] || {
    echo "ERROR: COGOS_PACK_ONLY=1 but no root image in workdir" >&2
    exit 4
  }
  echo "Using existing root image: $SFS_SOURCE ($(du -h "$SFS_SOURCE" | awk '{print $1}'))"
else
  forge_log_step "[8/9] Rebuild SquashFS: ${SQUASHFS_COMP} -> ${SFS_NAME:-rootfs} ($(du -sh "$WORK/rootfs" | awk '{print $1}') tree; 10-25 min, -progress below)"
  SFS_SOURCE="$(replay_sfs_write_path "$WORK/iso")"
  if [[ "${COGOS_XATTRS:-0}" == "1" ]]; then
    mksquashfs "$WORK/rootfs" "$SFS_SOURCE" -comp "$SQUASHFS_COMP" -b "$SQUASHFS_BLOCK" -noappend -all-root -progress
  else
    mksquashfs "$WORK/rootfs" "$SFS_SOURCE" -comp "$SQUASHFS_COMP" -b "$SQUASHFS_BLOCK" -noappend -all-root -no-xattrs -progress
  fi
  forge_log_step "[8/9] SquashFS rebuild complete: $SFS_SOURCE"
fi

forge_log_step "[9/9] Rebuild ISO (replay boot via adapter=${COGOS_REPLAY_ADAPTER:-debian-live-layout})"
build_iso_from_workdir "$WORK" "$REPLAY_ISO" "$OUT"

if forge_selector_present; then
  forge_emit_final_attestation
fi
