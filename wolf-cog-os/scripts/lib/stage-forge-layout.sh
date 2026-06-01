#!/usr/bin/env bash
# Stage /forge cockpit content into a rootfs tree for Forge ISO builds.
set -euo pipefail

stage_forge_layout() {
  local rootfs="${1:?rootfs path required}"
  local forge_src="${WOLF_FORGE_STAGING:-$WOLF_COGOS_ROOT/forge}"
  local scripts_src="$WOLF_COGOS_ROOT/scripts"
  local profiles_src="$WOLF_COGOS_ROOT/profiles/forge"

  if [[ ! -d "$forge_src" ]]; then
    echo "ERROR: Forge staging source missing: $forge_src" >&2
    return 3
  fi

  echo "[forge] staging cockpit layout into $rootfs/forge"
  mkdir -p \
    "$rootfs/forge/pipelines" \
    "$rootfs/forge/templates" \
    "$rootfs/forge/overlays" \
    "$rootfs/forge/governance" \
    "$rootfs/forge/output" \
    "$rootfs/forge/cache" \
    "$rootfs/forge/scripts/build" \
    "$rootfs/forge/scripts/build/lib"

  rsync -a \
    --exclude 'output/***' \
    --exclude 'cache/***' \
    "$forge_src/" "$rootfs/forge/"
  echo "[forge] staged forge registry tree"

  mkdir -p "$rootfs/forge/substrates" "$rootfs/forge/backends" "$rootfs/forge/governance"
  if [[ -f "$WOLF_FORGE_STAGING/substrates/registry.json" ]]; then
    cp "$WOLF_FORGE_STAGING/substrates/registry.json" "$rootfs/forge/substrates/registry.json"
  fi
  if [[ -d "$WOLF_FORGE_STAGING/substrates/schema" ]]; then
    rsync -a "$WOLF_FORGE_STAGING/substrates/schema/" "$rootfs/forge/substrates/schema/"
  fi
  if [[ -f "$WOLF_FORGE_STAGING/backends/registry.json" ]]; then
    cp "$WOLF_FORGE_STAGING/backends/registry.json" "$rootfs/forge/backends/registry.json"
  fi
  if [[ -f "$WOLF_FORGE_STAGING/replay-adapters/registry.json" ]]; then
    mkdir -p "$rootfs/forge/replay-adapters"
    cp "$WOLF_FORGE_STAGING/replay-adapters/registry.json" "$rootfs/forge/replay-adapters/registry.json"
  fi
  if [[ -f "$REPO_ROOT/.github/governance/substrate-evolution-ledger.json" ]]; then
    cp "$REPO_ROOT/.github/governance/substrate-evolution-ledger.json" "$rootfs/forge/governance/substrate-evolution-ledger.json"
  fi
  if [[ -f "$REPO_ROOT/wolf-cog-os/forge/governance/substrate-invariants.json" ]]; then
    mkdir -p "$rootfs/forge/governance"
    cp "$REPO_ROOT/wolf-cog-os/forge/governance/substrate-invariants.json" "$rootfs/forge/governance/substrate-invariants.json"
  fi

  if [[ -d "$profiles_src" ]]; then
    mkdir -p "$rootfs/forge/profiles"
    rsync -a "$profiles_src/" "$rootfs/forge/profiles/"
  fi

  local build_script
  for build_script in \
    build.sh \
    build-rootfs.sh \
    build_iso.sh \
    build-forge-installer.sh \
    patch_grub_merge.sh \
    paths.sh \
    validate-substrate.py \
    validate-pipeline.py \
    emit-forge-lineage.py \
    validate-replay-adapter.py \
    validate-lineage-reproducibility.py \
    run-forge-pipeline.sh \
    lib/resolve-pipeline-env.py \
    lib/forge-pipeline-run.sh \
    lib/emit-pipeline-outputs.sh; do
    if [[ -f "$scripts_src/$build_script" ]]; then
      cp "$scripts_src/$build_script" "$rootfs/forge/scripts/build/$build_script"
      chmod +x "$rootfs/forge/scripts/build/$build_script"
    fi
  done

  if [[ -d "$scripts_src/lib" ]]; then
    echo "[forge] staging build scripts/lib (may take a few minutes from DrvFs)..."
    rsync -a "$scripts_src/lib/" "$rootfs/forge/scripts/build/lib/"
    echo "[forge] build scripts/lib staged"
  fi

  if [[ -f "$REPO_ROOT/Makefile" ]]; then
    cp "$REPO_ROOT/Makefile" "$rootfs/forge/Makefile"
  fi

  mkdir -p "$rootfs/usr/local/bin"
  install -m 755 "$forge_src/scripts/forge-menu.sh" "$rootfs/usr/local/bin/forge-menu"
  install -m 755 "$forge_src/scripts/forge-run-pipeline.sh" "$rootfs/usr/local/bin/forge-run-pipeline"

  mkdir -p "$rootfs/etc/profile.d"
  cat >"$rootfs/etc/profile.d/forge-mode.sh" <<'EOF'
if [[ "${COGOS_FORGE_MODE:-0}" == "1" && -t 1 && -z "${FORGE_MENU_STARTED:-}" ]]; then
  export FORGE_MENU_STARTED=1
  echo "Forge Mode active. Run 'forge-menu' to open the pipeline cockpit."
fi
EOF

  echo "[forge] cockpit staged at $rootfs/forge"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  _stage_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  # shellcheck source=paths.sh
  source "$_stage_dir/paths.sh"
  stage_forge_layout "${1:?usage: stage-forge-layout.sh <rootfs>}"
fi
