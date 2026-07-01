#!/usr/bin/env python3
"""One-shot migration: wolf-cog-os command-ledger paths → cog-os (Nova CoG OS)."""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = REPO_ROOT / ".github" / "governance" / "command-ledger.json"

PATH_MAP = {
    "wolf-cog-os/scripts/build-rootfs.sh": "cog-os/forge/scripts/build-rootfs.sh",
    "wolf-cog-os/scripts/cogos-installer.sh": "cog-os/scripts/cogos-installer.sh",
    "wolf-cog-os/scripts/lib/profile-loader.sh": "cog-os/forge/scripts/lib/profile-loader.sh",
    "wolf-cog-os/scripts/validate-profile.py": "cog-os/forge/scripts/validate-profile.py",
    "wolf-cog-os/scripts/emit-profile-attestation.py": "cog-os/forge/scripts/lib/emit-profile-attestation.sh",
    "wolf-cog-os/scripts/test/forge-iso-smoke.sh": "cog-os/scripts/test/qemu-smoke.sh",
}

REMOVED_IDS = {
    "script.wolf-cog-os.build-forge-installer": "cog-os/forge/scripts/build-iso.sh",
    "script.wolf-cog-os.stage-forge-layout": "cog-os/forge/scripts/build-rootfs.sh",
    "script.wolf-cog-os.emit-forge-build-state": "cog-os/forge/scripts/lib/emit-profile-attestation.sh",
    "script.wolf-cog-os.promotion-dry-run": "cog-os/scripts/test/test-forge-profile-loader.py",
    "script.wolf-cog-os.validate-substrate": ".github/scripts/validate-substrate-evolution-ledger.py",
    "script.wolf-cog-os.validate-rootfs-backend": "cog-os/host/scripts/build_rootfs.sh",
    "script.wolf-cog-os.forge-platform-dashboard": "cog-os/forge/scripts/validate-profile.py",
}

CONSUMER_REPLACEMENTS = {
    "bash wolf-cog-os/scripts/lib/profile-loader.sh": "cog-os/forge/scripts/lib/profile-loader.sh",
    "python3 wolf-cog-os/scripts/validate-profile.py": "cog-os/forge/scripts/validate-profile.py",
    "python3 wolf-cog-os/scripts/emit-profile-attestation.py": "cog-os/forge/scripts/lib/emit-profile-attestation.sh",
    "forge-iso-smoke.sh": "qemu-smoke.sh",
    ".github/workflows/cogos-ci-public.yml": ".github/workflows/cogos-forge-gate.yml",
    ".github/workflows/cogos-ci-selfhosted.yml": ".github/workflows/cogos-forge-gate.yml",
    ".github/workflows/cogos-rc.yml": ".github/workflows/cogos-forge-gate.yml",
}


def _replace_in_obj(obj, mapping: dict[str, str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                for old, new in mapping.items():
                    if old in value:
                        obj[key] = value.replace(old, new)
            else:
                _replace_in_obj(value, mapping)
    elif isinstance(obj, list):
        for item in obj:
            _replace_in_obj(item, mapping)


def main() -> int:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    _replace_in_obj(ledger, PATH_MAP)
    _replace_in_obj(ledger, CONSUMER_REPLACEMENTS)

    for cmd in ledger.get("commands", []):
        cmd_id = cmd.get("id", "")
        if cmd_id in REMOVED_IDS:
            replacement = REMOVED_IDS[cmd_id]
            cmd["deprecation"] = {
                "status": "removed",
                "replacement": replacement,
            }
            cmd["consumers"] = []
            cmd["owner"] = replacement
            if cmd.get("invocation", {}).get("type") == "script_path":
                cmd["invocation"]["path"] = replacement
        elif cmd_id.startswith("script.wolf-cog-os."):
            dep = cmd.setdefault("deprecation", {})
            if dep.get("status") != "removed":
                dep["status"] = "active"
                dep["replacement"] = dep.get("replacement") or "cog-os/"

    LEDGER_PATH.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {LEDGER_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
