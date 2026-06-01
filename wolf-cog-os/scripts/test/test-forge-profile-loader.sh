#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/profile-loader.sh
source "$SCRIPT_DIR/../lib/profile-loader.sh"

assert_eq() {
  local expected="$1"
  local actual="$2"
  local msg="$3"
  if [[ "$expected" != "$actual" ]]; then
    echo "ASSERT FAIL: $msg (expected=$expected actual=$actual)" >&2
    exit 1
  fi
}

unset COGOS_FORGE_PROFILE
unset COGOS_BOOT_PROFILE
assert_eq "forge-selfhosted" "$(forge_resolve_profile_id "")" "default profile"
assert_eq "default" "$(forge_profile_source "")" "default source"

export COGOS_BOOT_PROFILE="forge-dev"
assert_eq "forge-dev" "$(forge_resolve_profile_id "")" "boot profile selector"
assert_eq "env.COGOS_BOOT_PROFILE" "$(forge_profile_source "")" "boot source"

export COGOS_FORGE_PROFILE="forge-selfhosted"
assert_eq "forge-selfhosted" "$(forge_resolve_profile_id "")" "forge profile env selector"
assert_eq "env.COGOS_FORGE_PROFILE" "$(forge_profile_source "")" "forge env source"

assert_eq "forge-canary" "$(forge_resolve_profile_id "forge-canary")" "cli selector"
assert_eq "cli" "$(forge_profile_source "forge-canary")" "cli source"

echo "forge profile loader precedence checks passed"
