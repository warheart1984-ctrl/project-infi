#!/usr/bin/env bash
# Stamp release_manifest.json for Wolf CoG OS regular edition with full runtime.
set -euo pipefail

update_full_runtime_manifest() {
  local manifest_root="${1:-}"
  local tag="${2:-wolf-cog-os-full-1.0}"
  local build_date="${3:-$(date -u +%Y-%m-%d)}"
  local boot_profile="${4:-metal}"
  local graphical="${COGOS_GRAPHICAL_INSTALL:-0}"
  local di_install="${COGOS_DI_INSTALL:-0}"
  local manifest_path="$manifest_root/config/release_manifest.json"

  [[ -d "$manifest_root" ]] || {
    echo "ERROR: manifest root missing: $manifest_root" >&2
    return 1
  }

  python3 <<PY
import json
from pathlib import Path

root = Path(r"$manifest_root")
manifest_path = root / "config/release_manifest.json"
graphical = "$graphical" == "1" or "$di_install" == "1" or "$boot_profile" == "debian"
if not manifest_path.exists():
    manifest = {
        "product": "Wolf CoG OS",
        "edition": "Regular (Full Runtime)",
        "version": "$tag",
        "build_date": "$build_date",
        "release_name": "Wolf CoG OS Full Runtime",
        "components": {},
        "verification": [],
    }
else:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))

manifest["version"] = "$tag"
manifest["build_date"] = "$build_date"
manifest["release_name"] = "Wolf CoG OS Regular Edition (Full Runtime)"
manifest.setdefault("components", {})
components = manifest["components"]
components["boot_profile"] = "$boot_profile"
components["metal_installer"] = "cogos-install_apply_v1"
components["daily_driver"] = "full_nova_stack_v1"
components["install_hook"] = "cogos-install-finish"
components["live_boot_contract"] = "systemd_pid1_pre_pack_validated_v1"
components["runtime_plane"] = "governed_full_stack_v1"
components["cognitive_runtime_family"] = "v3_nova_cortex_unified"
components["nova_cortex"] = "v3_nova_wolf_unified"
components["cognitive_runtime_bridge"] = "opt/cogos/runtime/src/cogos_runtime_bridge.py"
components["cognitive_runtime"] = "v3_nova_cortex"
components.pop("surprise_installer", None)
if graphical:
    components["graphical_install"] = "debian_di_preseed_late_command_v1"
    components["calamares_hook"] = "shellprocess@cogos-finish"
    components["debian_di_hook"] = "initrd_embedded_preseed_late_command_v1"
    components["install_paths"] = ["debian_gtk_di", "debian_text_di", "cogos-install_apply"]
else:
    components.pop("graphical_install", None)
    components.pop("calamares_hook", None)
    components.pop("debian_di_hook", None)
    components.pop("install_paths", None)
manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(f"release_manifest.json updated: {manifest_path}")
PY
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  update_full_runtime_manifest "${1:-}" "${2:-}" "${3:-}" "${4:-metal}"
fi
