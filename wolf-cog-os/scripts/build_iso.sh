#!/usr/bin/env bash
# Shared xorriso ISO packaging: replay boot from source ISO, fallbacks on GPT errors.
set -euo pipefail

_build_iso_replay_candidates() {
  local primary="$1"
  local candidate

  printf '%s\n' "$primary"
  if [[ -n "${COGOS_SUBSTRATE_ISO:-}" && "$COGOS_SUBSTRATE_ISO" != "$primary" && "$COGOS_SUBSTRATE_ISO" != "${COGOS_BOOT_REPLAY_ISO:-}" ]]; then
    printf '%s\n' "$COGOS_SUBSTRATE_ISO"
  fi
  if [[ -n "${COGOS_BOOT_REPLAY_ISO:-}" && "$COGOS_BOOT_REPLAY_ISO" != "$primary" ]]; then
    printf '%s\n' "$COGOS_BOOT_REPLAY_ISO"
  fi
  if [[ -n "${DEBIAN_BASE_ISO:-}" && "$DEBIAN_BASE_ISO" != "$primary" && "$DEBIAN_BASE_ISO" != "${COGOS_BOOT_REPLAY_ISO:-}" ]]; then
    printf '%s\n' "$DEBIAN_BASE_ISO"
  fi
  if [[ -f "${HOME}/debian-live-13.5.0-amd64-cinnamon.iso" ]]; then
    candidate="${HOME}/debian-live-13.5.0-amd64-cinnamon.iso"
    if [[ "$candidate" != "$primary" && "$candidate" != "${COGOS_BOOT_REPLAY_ISO:-}" && "$candidate" != "${DEBIAN_BASE_ISO:-}" ]]; then
      printf '%s\n' "$candidate"
    fi
  fi
}

build_iso_mkisofs_fallback() {
  local work_iso="$1"
  local replay_iso="$2"
  local out="$3"
  local recipe

  recipe="$(xorriso -indev "$replay_iso" -report_el_torito as_mkisofs 2>/dev/null | grep -v modification-date || true)"
  if [[ -z "$recipe" ]]; then
    echo "ERROR: could not read El Torito recipe from $replay_iso" >&2
    return 1
  fi

  echo "Using mkisofs fallback (source: $(basename "$replay_iso"))"
  rm -f "$out" 2>/dev/null || true
  # shellcheck disable=SC2086
  (
    cd "$work_iso"
    xorriso -as mkisofs $recipe -o "$out" .
  )
}

build_iso_from_workdir() {
  local work="$1"
  local replay_iso="$2"
  local out="$3"
  local work_iso="$work/iso"
  local candidate
  local size_source="$replay_iso"

  rm -f "$out" 2>/dev/null || true

  while IFS= read -r candidate; do
    [[ -f "$candidate" ]] || continue
    echo "Trying xorriso boot replay from $(basename "$candidate")"
    if xorriso -indev "$candidate" -outdev "$out" \
      -boot_image any replay \
      -map "$work_iso" "/" \
      -commit >/dev/null 2>&1; then
      echo "Built with xorriso boot replay: $out (boot from $(basename "$candidate"))"
      sha256sum "$out" | tee "${out}.sha256"
      verify_iso_size "$size_source" "$out"
      return 0
    fi
    rm -f "$out" 2>/dev/null || true
  done < <(_build_iso_replay_candidates "$replay_iso")

  while IFS= read -r candidate; do
    [[ -f "$candidate" ]] || continue
    if build_iso_mkisofs_fallback "$work_iso" "$candidate" "$out"; then
      echo "Built with mkisofs fallback: $out (boot from $(basename "$candidate"))"
      sha256sum "$out" | tee "${out}.sha256"
      verify_iso_size "$size_source" "$out"
      return 0
    fi
    rm -f "$out" 2>/dev/null || true
  done < <(_build_iso_replay_candidates "$replay_iso")

  echo "ERROR: xorriso failed to build $out" >&2
  return 6
}
