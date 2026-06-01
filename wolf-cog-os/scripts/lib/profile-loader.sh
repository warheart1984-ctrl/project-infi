#!/usr/bin/env bash
set -euo pipefail

forge_profile_default_id() {
  echo "forge-selfhosted"
}

forge_profile_root() {
  local root="${1:-wolf-cog-os/profiles/forge}"
  echo "$root"
}

forge_resolve_profile_id() {
  local cli_profile="${1:-}"
  if [[ -n "$cli_profile" ]]; then
    echo "$cli_profile"
    return 0
  fi

  if [[ -n "${COGOS_FORGE_PROFILE:-}" ]]; then
    echo "$COGOS_FORGE_PROFILE"
    return 0
  fi

  if [[ -n "${COGOS_BOOT_PROFILE:-}" && "${COGOS_BOOT_PROFILE}" == forge* ]]; then
    echo "$COGOS_BOOT_PROFILE"
    return 0
  fi

  forge_profile_default_id
}

forge_profile_source() {
  local cli_profile="${1:-}"
  if [[ -n "$cli_profile" ]]; then
    echo "cli"
    return 0
  fi
  if [[ -n "${COGOS_FORGE_PROFILE:-}" ]]; then
    echo "env.COGOS_FORGE_PROFILE"
    return 0
  fi
  if [[ -n "${COGOS_BOOT_PROFILE:-}" && "${COGOS_BOOT_PROFILE}" == forge* ]]; then
    echo "env.COGOS_BOOT_PROFILE"
    return 0
  fi
  echo "default"
}

forge_profile_path() {
  local profile_id="${1:?profile id required}"
  local profile_root="${2:-$(forge_profile_root)}"
  echo "${profile_root}/${profile_id}.yaml"
}

forge_emit_resolution_json() {
  local cli_profile="${1:-}"
  local profile_root="${2:-$(forge_profile_root)}"
  local profile_id
  profile_id="$(forge_resolve_profile_id "$cli_profile")"
  local source
  source="$(forge_profile_source "$cli_profile")"
  local path
  path="$(forge_profile_path "$profile_id" "$profile_root")"
  printf '{\n'
  printf '  "profile_id": "%s",\n' "$profile_id"
  printf '  "source": "%s",\n' "$source"
  printf '  "profile_path": "%s"\n' "$path"
  printf '}\n'
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  cli_profile="${1:-}"
  forge_emit_resolution_json "$cli_profile"
fi
