#!/usr/bin/env bash
# Ensure COGOS_PAYLOAD has a complete runtime tree before ISO build.
set -euo pipefail

# shellcheck source=lib/cogos-systemd-stack.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/cogos-systemd-stack.sh"
# shellcheck source=lib/normalize-boot-stack-lf.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/normalize-boot-stack-lf.sh"

payload_tree_bytes() {
  local root="$1"
  du -sb "$root" 2>/dev/null | awk '{print $1}'
}

payload_wrapper_count() {
  local root="$1"
  find "$root/usr/local/bin" -maxdepth 1 -name 'cogos-*' -type f 2>/dev/null | wc -l
}

copy_payload_tree_from_rootfs() {
  local src="$1"
  local cache="$2"
  local include_systemd_units="${3:-1}"

  mkdir -p "$cache/opt/cogos" "$cache/usr/local/bin" "$cache/usr/lib/cogos" "$cache/etc/systemd/system"

  if [[ -d "$src/opt/cogos" ]]; then
    rsync -a \
      --exclude 'memory/' \
      --exclude '**/__pycache__/' \
      --exclude '*.pyc' \
      "$src/opt/cogos/" "$cache/opt/cogos/"
  fi

  if [[ -d "$src/usr/local/bin" ]]; then
    rsync -a "$src/usr/local/bin"/cogos-* "$cache/usr/local/bin/" 2>/dev/null || true
    chmod +x "$cache/usr/local/bin"/cogos-runtime-start "$cache/usr/local/bin"/cogos-runtime-stop 2>/dev/null || true
  fi

  if [[ -d "$src/usr/lib/cogos" ]]; then
    mkdir -p "$cache/usr/lib/cogos"
    for launcher in "${COGOS_BOOT_LAUNCHERS[@]}"; do
      [[ -f "$src/usr/lib/cogos/$launcher" ]] || continue
      rsync -a "$src/usr/lib/cogos/$launcher" "$cache/usr/lib/cogos/"
      chmod +x "$cache/usr/lib/cogos/$launcher"
    done
  fi

  if [[ "$include_systemd_units" == "1" ]]; then
    local rel name
    for rel in "${COGOS_BOOT_HARDENING_ARTIFACTS[@]}"; do
      name="${rel#etc/systemd/system/}"
      if [[ -f "$src/etc/systemd/system/$name" ]]; then
        mkdir -p "$cache/etc/systemd/system/$(dirname "$name")"
        rsync -a "$src/etc/systemd/system/$name" "$cache/etc/systemd/system/$name"
        chmod 644 "$cache/etc/systemd/system/$name" 2>/dev/null || true
      fi
    done
  fi

  if [[ -f "$src/opt/cogos/config/governance_boot.json" ]]; then
    mkdir -p "$cache/opt/cogos/config"
    rsync -a "$src/opt/cogos/config/governance_boot.json" "$cache/opt/cogos/config/"
  fi

  if [[ -f "$src/etc/cog/governance.json" ]]; then
    mkdir -p "$cache/etc/cog" "$cache/etc/cogos"
    rsync -a "$src/etc/cog/governance.json" "$cache/etc/cog/"
    rsync -a "$src/etc/cog/governance.json" "$cache/etc/cogos/governance.json"
  fi

  if [[ "$include_systemd_units" == "1" ]]; then
    local rel name
    for rel in "${COGOS_BOOT_STACK_UNITS[@]}"; do
      name="${rel#etc/systemd/system/}"
      if [[ -f "$src/etc/systemd/system/$name" ]]; then
        mkdir -p "$cache/etc/systemd/system/$(dirname "$name")"
        rsync -a "$src/etc/systemd/system/$name" "$cache/etc/systemd/system/$name"
        chmod 644 "$cache/etc/systemd/system/$name" 2>/dev/null || true
      fi
    done
  fi

  for unit in cogos-runtime.service cogos-first-boot.service; do
    if [[ "$include_systemd_units" == "1" && -f "$src/etc/systemd/system/$unit" ]]; then
      mkdir -p "$cache/etc/systemd/system"
      rsync -a "$src/etc/systemd/system/$unit" "$cache/etc/systemd/system/"
    fi
  done
}

  strip_legacy_sysv_from_payload_cache() {
  local cache="$1"
  # Old workdir seeds may still carry SysV hooks; repo payload no longer ships them.
  rm -f "$cache/etc/init.d/90cogos" 2>/dev/null || true
  rmdir "$cache/etc/init.d" 2>/dev/null || true
  # Substrate drop-ins removed in 3.5+ (deadlocked first boot on metal).
  rm -f \
    "$cache/etc/systemd/system/accounts-daemon.service.d/cogos-firstboot.conf" \
    "$cache/etc/systemd/system/dbus.service.d/cogos-firstboot.conf" \
    "$cache/etc/systemd/system/systemd-logind.service.d/cogos-firstboot.conf" \
    "$cache/etc/systemd/system/polkit.service.d/cogos-firstboot.conf" 2>/dev/null || true
}

payload_source_candidates() {
  cat <<EOF
${COGOS_PAYLOAD_SOURCE:-}
${COGOS_SURPRISE_WORK:-${HOME}/.cogos-surprise-work-daily-driver-1.6-surprise}/rootfs
${HOME}/.cogos-surprise-work-daily-driver-1.6-surprise/rootfs
${COGOS_UNIVERSAL_WORK:-${HOME}/.cogos-universal-installer-work}/rootfs
${COGOS_METAL_WORK:-${HOME}/.cogos-metal-installer-work}/rootfs
${HOME}/.ground-up-work/rootfs-working
EOF
}

best_payload_rootfs() {
  local candidate best="" best_wrappers=0 wrappers
  while IFS= read -r candidate; do
    [[ -n "$candidate" ]] || continue
    [[ -x "$candidate/opt/cogos/bin/cognitive_init" ]] || continue
    wrappers="$(payload_wrapper_count "$candidate")"
    if (( wrappers > best_wrappers )); then
      best="$candidate"
      best_wrappers=$wrappers
    fi
  done < <(payload_source_candidates)
  [[ -n "$best" ]] || return 1
  printf '%s' "$best"
}

restore_payload_from_workdir() {
  local cache="$1"
  local src
  src="$(best_payload_rootfs)" || return 1
  echo "[payload] restoring cache from workdir payload tree: $src ($(payload_wrapper_count "$src") wrappers)"
  copy_payload_tree_from_rootfs "$src" "$cache" 0
  return 0
}

seed_payload_from_surprise() {
  local cache="${1:-${HOME}/.cogos-payload-cache}"
  local src
  src="$(best_payload_rootfs)" || {
    echo "ERROR: no surprise/universal/metal workdir rootfs with cognitive_init found" >&2
    return 1
  }
  echo "[payload] seeding cache from full runtime rootfs: $src"
  copy_payload_tree_from_rootfs "$src" "$cache" 0
}

ensure_payload_ready() {
  local repo_payload="${1:-}"
  local cache="${2:-${HOME}/.cogos-payload-cache}"
  local min_bytes="${3:-400000}"
  local min_wrappers="${COGOS_PAYLOAD_MIN_WRAPPERS:-40}"
  local cache_bytes wrapper_count

  mkdir -p "$cache"

  if [[ "${COGOS_PAYLOAD_SEED_FROM_SURPRISE:-1}" == "1" ]]; then
    seed_payload_from_surprise "$cache" || return 1
  fi

  if [[ -d "$repo_payload/opt/cogos" ]]; then
    echo "[payload] overlaying repo payload onto cache"
    copy_payload_tree_from_rootfs "$repo_payload" "$cache"
  fi

  cache_bytes="$(payload_tree_bytes "$cache")"
  wrapper_count="$(payload_wrapper_count "$cache")"
  if [[ -z "$cache_bytes" || "$cache_bytes" -lt "$min_bytes" || ! -x "$cache/opt/cogos/bin/cognitive_init" || "$wrapper_count" -lt "$min_wrappers" ]]; then
    restore_payload_from_workdir "$cache" || {
      echo "ERROR: payload cache incomplete and no workdir rootfs found to restore from" >&2
      echo "ERROR: run: bash wolf-cog-os/scripts/restore-payload-cache.sh" >&2
      return 1
    }
    if [[ -d "$repo_payload/opt/cogos" ]]; then
      copy_payload_tree_from_rootfs "$repo_payload" "$cache"
    fi
  fi

  strip_legacy_sysv_from_payload_cache "$cache"
  normalize_boot_stack_lf "$cache"

  cache_bytes="$(payload_tree_bytes "$cache")"
  wrapper_count="$(payload_wrapper_count "$cache")"
  if [[ -z "$cache_bytes" || "$cache_bytes" -lt "$min_bytes" ]]; then
    echo "ERROR: payload cache too small (${cache_bytes:-0} bytes): $cache" >&2
    return 1
  fi

  if [[ ! -x "$cache/opt/cogos/bin/cognitive_init" ]]; then
    echo "ERROR: payload cache missing cognitive_init: $cache" >&2
    return 1
  fi

  if [[ "$wrapper_count" -lt "$min_wrappers" ]]; then
    echo "ERROR: payload cache has only $wrapper_count cogos-* wrappers (need >= $min_wrappers)" >&2
    return 1
  fi

  for launcher in "${COGOS_BOOT_LAUNCHERS[@]}"; do
    if [[ ! -x "$cache/usr/lib/cogos/$launcher" ]]; then
      echo "ERROR: payload cache missing /usr/lib/cogos/$launcher" >&2
      return 1
    fi
  done

  for unit in cogos-firstboot.service cogos-governance.service cogos-spine.service cogos-observer.service cogos-boot-hardening.service; do
    if [[ ! -f "$cache/etc/systemd/system/$unit" ]]; then
      echo "ERROR: payload cache missing $unit" >&2
      return 1
    fi
  done

  verify_cogos_boot_stack_present "$cache" || {
    echo "ERROR: payload cache missing one or more boot stack artifacts (need $(cogos_boot_stack_count))" >&2
    return 1
  }

  if [[ ! -x "$cache/usr/local/bin/cogos-runtime-start" ]]; then
    echo "ERROR: payload cache missing cogos-runtime-start" >&2
    return 1
  fi

  export COGOS_PAYLOAD="$cache"
  echo "[payload] ready: $COGOS_PAYLOAD ($(du -sh "$COGOS_PAYLOAD" | awk '{print $1}'), $(find "$COGOS_PAYLOAD" -type f | wc -l) files, $wrapper_count wrappers)"
}
