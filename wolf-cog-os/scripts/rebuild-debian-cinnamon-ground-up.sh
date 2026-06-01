#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"
# shellcheck source=lib/live-systemd-init.sh
source "$SCRIPT_DIR/lib/live-systemd-init.sh"
# shellcheck source=patch_calamares_surprise.sh
source "$SCRIPT_DIR/patch_calamares_surprise.sh"

STAGE="${STAGE:-preflight}"
DRY_RUN=1
SOURCE_ISO="${SOURCE_ISO:-$DEBIAN_BASE_ISO}"
WORK_DIR="${WORK_DIR:-/tmp/wolf-cog-os-ground-up}"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_ROOT="${ARTIFACT_ROOT:-$WOLF_COGOS_ROOT/artifacts/ground-up/$RUN_ID}"
PAYLOAD_DIR="${PAYLOAD_DIR:-$WOLF_PAYLOAD}"
PLYMOUTH_POLICY="${PLYMOUTH_POLICY:-optional}"
SURPRISE_INSTALL="${SURPRISE_INSTALL:-1}"

usage() {
  cat <<'USAGE'
Usage:
  bash wolf-cog-os/scripts/rebuild-debian-cinnamon-ground-up.sh [options]

Options:
  --stage <preflight|extract|rootfs|payload|boot|pack|verify|all>
  --source-iso <path>
  --work-dir <path>
  --artifact-root <path>
  --payload-dir <path>
  --plymouth-policy <required|optional|forbidden>
  --no-surprise          Skip Calamares surprise hook wiring in boot stage
  --run                 Execute writes (default is dry-run)
  --dry-run             Explicit dry-run mode
  -h, --help

Behavior:
  - Dry-run is default for safety.
  - No host-destructive actions are executed by default.
  - Stages are incremental and emit stage manifests under artifact root.
USAGE
}

log() {
  printf '[ground-up][%s] %s\n' "$1" "$2"
}

die() {
  printf '[ground-up][ERROR] %s\n' "$1" >&2
  exit "${2:-1}"
}

run_cmd() {
  local stage="$1"
  shift
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "$stage" "DRY-RUN: $*"
  else
    log "$stage" "RUN: $*"
    "$@"
  fi
}

require_tools() {
  local tools=(bash python3 sha256sum xorriso unsquashfs mksquashfs rsync)
  local t
  for t in "${tools[@]}"; do
    command -v "$t" >/dev/null 2>&1 || die "missing required tool: $t" 2
  done
}

safe_mkdir() {
  local stage="$1"
  local p="$2"
  run_cmd "$stage" mkdir -p "$p"
}

stage_dir() {
  local stage="$1"
  printf '%s/stage-%s' "$ARTIFACT_ROOT" "$stage"
}

emit_manifest() {
  local stage="$1"
  local status="$2"
  local dir
  dir="$(stage_dir "$stage")"
  mkdir -p "$dir"
  python3 - "$dir/manifest.json" <<PY
import json
import os
import sys
from datetime import datetime, timezone

out = sys.argv[1]
data = {
    "stage": "${stage}",
    "status": "${status}",
    "run_id": "${RUN_ID}",
    "dry_run": ${DRY_RUN},
    "source_iso": "${SOURCE_ISO}",
    "work_dir": "${WORK_DIR}",
    "artifact_root": "${ARTIFACT_ROOT}",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
}
with open(out, "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY
}

emit_run_metadata() {
  mkdir -p "$ARTIFACT_ROOT"
  python3 - "$ARTIFACT_ROOT/run-metadata.json" <<PY
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone

def cmd_or_na(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except Exception:
        return "n/a"

meta = {
    "run_id": "${RUN_ID}",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "dry_run": ${DRY_RUN},
    "stage_request": "${STAGE}",
    "source_iso": "${SOURCE_ISO}",
    "work_dir": "${WORK_DIR}",
    "artifact_root": "${ARTIFACT_ROOT}",
    "payload_dir": "${PAYLOAD_DIR}",
    "plymouth_policy": "${PLYMOUTH_POLICY}",
    "host": {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "kernel": platform.release(),
    },
    "tool_versions": {
        "bash": cmd_or_na(["bash", "--version"]).splitlines()[0],
        "xorriso": cmd_or_na(["xorriso", "-version"]).splitlines()[0] if cmd_or_na(["xorriso", "-version"]) != "n/a" else "n/a",
        "unsquashfs": cmd_or_na(["unsquashfs", "-version"]).splitlines()[0] if cmd_or_na(["unsquashfs", "-version"]) != "n/a" else "n/a",
        "mksquashfs": cmd_or_na(["mksquashfs", "-version"]).splitlines()[0] if cmd_or_na(["mksquashfs", "-version"]) != "n/a" else "n/a",
    },
}
with open(sys.argv[1], "w", encoding="utf-8", newline="\n") as f:
    json.dump(meta, f, indent=2)
    f.write("\n")
PY
}

write_source_iso_hash() {
  local out="$ARTIFACT_ROOT/source-iso.sha256"
  if [[ ! -f "$SOURCE_ISO" ]]; then
    die "source ISO not found: $SOURCE_ISO" 3
  fi
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log preflight "DRY-RUN: sha256sum \"$SOURCE_ISO\" > \"$out\""
  else
    sha256sum "$SOURCE_ISO" >"$out"
  fi
}

check_lf_normalization() {
  local checks=(
    "$SCRIPT_DIR/rebuild-debian-cinnamon-ground-up.sh"
    "$SCRIPT_DIR/validate-live-boot-integrity.sh"
  )
  python3 - "${checks[@]}" <<'PY'
import pathlib
import sys

bad = []
for p in sys.argv[1:]:
    data = pathlib.Path(p).read_bytes()
    if b"\r\n" in data:
        bad.append(p)
if bad:
    print("CRLF detected in build-critical files:")
    for b in bad:
        print(b)
    raise SystemExit(9)
PY
}

parse_args() {
  while (($# > 0)); do
    case "$1" in
      --stage)
        STAGE="${2:-}"
        shift 2
        ;;
      --stage=*)
        STAGE="${1#*=}"
        shift
        ;;
      --source-iso)
        SOURCE_ISO="${2:-}"
        shift 2
        ;;
      --source-iso=*)
        SOURCE_ISO="${1#*=}"
        shift
        ;;
      --work-dir)
        WORK_DIR="${2:-}"
        shift 2
        ;;
      --work-dir=*)
        WORK_DIR="${1#*=}"
        shift
        ;;
      --artifact-root)
        ARTIFACT_ROOT="${2:-}"
        shift 2
        ;;
      --artifact-root=*)
        ARTIFACT_ROOT="${1#*=}"
        shift
        ;;
      --payload-dir)
        PAYLOAD_DIR="${2:-}"
        shift 2
        ;;
      --payload-dir=*)
        PAYLOAD_DIR="${1#*=}"
        shift
        ;;
      --plymouth-policy)
        PLYMOUTH_POLICY="${2:-}"
        shift 2
        ;;
      --plymouth-policy=*)
        PLYMOUTH_POLICY="${1#*=}"
        shift
        ;;
      --no-surprise)
        SURPRISE_INSTALL=0
        shift
        ;;
      --run)
        DRY_RUN=0
        shift
        ;;
      --dry-run)
        DRY_RUN=1
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        die "unknown argument: $1" 2
        ;;
    esac
  done
}

resolve_stage_list() {
  case "$STAGE" in
    preflight) STAGE_LIST=(preflight) ;;
    extract) STAGE_LIST=(preflight extract) ;;
    rootfs) STAGE_LIST=(preflight extract rootfs) ;;
    payload) STAGE_LIST=(preflight extract rootfs payload) ;;
    boot) STAGE_LIST=(preflight extract rootfs payload boot) ;;
    verify) STAGE_LIST=(preflight extract rootfs payload boot verify) ;;
    pack) STAGE_LIST=(preflight extract rootfs payload boot verify pack) ;;
    all) STAGE_LIST=(preflight extract rootfs payload boot verify pack) ;;
    *) die "invalid stage: $STAGE" 2 ;;
  esac
}

run_preflight() {
  log preflight "starting preflight checks"
  require_tools
  check_lf_normalization
  [[ -n "$SOURCE_ISO" ]] || die "source ISO path is empty" 3
  [[ -f "$SOURCE_ISO" ]] || die "source ISO missing: $SOURCE_ISO" 3
  [[ -d "$PAYLOAD_DIR" ]] || die "payload dir missing: $PAYLOAD_DIR" 3

  safe_mkdir preflight "$ARTIFACT_ROOT"
  safe_mkdir preflight "$WORK_DIR"
  safe_mkdir preflight "$WORK_DIR/iso"
  safe_mkdir preflight "$WORK_DIR/rootfs"
  safe_mkdir preflight "$WORK_DIR/rootfs-working"
  safe_mkdir preflight "$(stage_dir preflight)"

  emit_run_metadata
  write_source_iso_hash
  emit_manifest preflight proven
  log preflight "preflight complete"
}

run_extract() {
  log extract "extracting source ISO to work tree"
  safe_mkdir extract "$WORK_DIR/iso"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    run_cmd extract xorriso -osirrox on -indev "$SOURCE_ISO" -extract / "$WORK_DIR/iso"
  else
    xorriso -osirrox on -indev "$SOURCE_ISO" -extract / "$WORK_DIR/iso" >/dev/null
    chmod -R u+w "$WORK_DIR/iso"
  fi
  emit_manifest extract proven
}

discover_squashfs() {
  local p
  for p in \
    "$WORK_DIR/iso/live/filesystem.squashfs" \
    "$WORK_DIR/iso/live/filesystem.squashfs"; do
    [[ -f "$p" ]] && {
      printf '%s\n' "$p"
      return 0
    }
  done
  return 1
}

run_rootfs() {
  log rootfs "extracting live rootfs"
  local sfs
  sfs="$(discover_squashfs)" || die "unable to locate filesystem.squashfs in extracted ISO" 4
  mkdir -p "$(stage_dir rootfs)"
  printf '%s\n' "$sfs" >"$(stage_dir rootfs)/squashfs-source.txt"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    run_cmd rootfs unsquashfs -no-xattrs -f -d "$WORK_DIR/rootfs" "$sfs"
  else
    unsquashfs -no-xattrs -f -d "$WORK_DIR/rootfs" "$sfs"
  fi
  emit_manifest rootfs proven
}

run_payload() {
  log payload "overlaying payload into working rootfs"
  mkdir -p "$(stage_dir payload)"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    run_cmd payload rsync -aH --delete "$WORK_DIR/rootfs/" "$WORK_DIR/rootfs-working/"
    run_cmd payload rsync -aH "$PAYLOAD_DIR/" "$WORK_DIR/rootfs-working/"
  else
    rsync -aH --delete "$WORK_DIR/rootfs/" "$WORK_DIR/rootfs-working/"
    rsync -aH "$PAYLOAD_DIR/" "$WORK_DIR/rootfs-working/"
    (
      cd "$WORK_DIR/rootfs-working"
      find . -type f | LC_ALL=C sort >"$(stage_dir payload)/changed-paths.txt"
    )
  fi
  emit_manifest payload proven
}

run_boot() {
  log boot "applying live-safe init contract and surprise runtime hooks"
  mkdir -p "$(stage_dir boot)"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    run_cmd boot restore_live_systemd_init_links "$WORK_DIR/rootfs-working"
    if [[ "$SURPRISE_INSTALL" == "1" ]]; then
      run_cmd boot patch_calamares_surprise "$WORK_DIR/rootfs-working"
    fi
  else
    restore_live_systemd_init_links "$WORK_DIR/rootfs-working" || die "failed to pin live init to systemd" 6
    if [[ "$SURPRISE_INSTALL" == "1" ]]; then
      patch_calamares_surprise "$WORK_DIR/rootfs-working"
    fi
  fi
  {
    echo "init-contract-allowed-targets:"
    echo "  - /lib/systemd/systemd"
    echo "  - /usr/lib/systemd/systemd (merged-usr canonical)"
    echo "plymouth-policy: $PLYMOUTH_POLICY"
    echo "surprise-install: $SURPRISE_INSTALL"
    echo "grub-squashfs-path-contract: /live/filesystem.squashfs"
  } >"$(stage_dir boot)/boot-policy-report.txt"
  emit_manifest boot proven
}

run_pack() {
  log pack "pack stage blocked unless live-boot integrity gate passed"
  mkdir -p "$(stage_dir pack)"
  local verify_proof="$(stage_dir verify)/validation.json"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    run_cmd pack test -f "$verify_proof"
    {
      echo "pack stage requires stage-verify/validation.json"
      echo "run: --stage verify --run before --stage pack --run"
      echo "or use build-universal-installer.sh for full ISO emission"
    } >"$(stage_dir pack)/pack-plan.txt"
    emit_manifest pack asserted
    return 0
  fi

  [[ -f "$verify_proof" ]] || die "pack blocked: missing verify proof at $verify_proof (run verify stage first)" 7
  {
    echo "verify proof present: $verify_proof"
    echo "full ISO pack not yet implemented in ground-up scaffold"
    echo "use: bash wolf-cog-os/scripts/build-wolf-cog-os-full.sh"
  } >"$(stage_dir pack)/pack-plan.txt"
  emit_manifest pack asserted
  log pack "integrity gate passed; use build-wolf-cog-os-full.sh to emit final ISO"
}

run_verify() {
  log verify "running boot-critical integrity validator"
  mkdir -p "$(stage_dir verify)"
  local validator="$SCRIPT_DIR/validate-live-boot-integrity.sh"
  [[ -f "$validator" ]] || die "validator not found: $validator" 5
  if [[ "$DRY_RUN" -eq 1 ]]; then
    run_cmd verify bash "$validator" \
      --rootfs "$WORK_DIR/rootfs-working" \
      --iso-tree "$WORK_DIR/iso" \
      --plymouth-policy "$PLYMOUTH_POLICY" \
      --proof-dir "$(stage_dir verify)"
  else
    bash "$validator" \
      --rootfs "$WORK_DIR/rootfs-working" \
      --iso-tree "$WORK_DIR/iso" \
      --plymouth-policy "$PLYMOUTH_POLICY" \
      --proof-dir "$(stage_dir verify)"
  fi
  emit_manifest verify proven
}

main() {
  parse_args "$@"
  resolve_stage_list
  log preflight "stage request: $STAGE (dry-run=$DRY_RUN)"
  log preflight "artifact root: $ARTIFACT_ROOT"
  log preflight "work dir: $WORK_DIR"

  local s
  for s in "${STAGE_LIST[@]}"; do
    case "$s" in
      preflight) run_preflight ;;
      extract) run_extract ;;
      rootfs) run_rootfs ;;
      payload) run_payload ;;
      boot) run_boot ;;
      pack) run_pack ;;
      verify) run_verify ;;
      *) die "unsupported stage in execution list: $s" 2 ;;
    esac
  done

  log done "completed stages: ${STAGE_LIST[*]}"
  log done "proof scaffold: $ARTIFACT_ROOT"
}

main "$@"
