#!/usr/bin/env python3
"""Cross-platform forge profile loader contract tests."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    loader = repo_root / "cog-os" / "forge" / "scripts" / "lib" / "profile-loader.sh"
    loader_arg = loader.relative_to(repo_root).as_posix()
    if not loader.is_file():
        print(f"missing profile loader: {loader}", file=sys.stderr)
        return 1

    for profile in ("metal", "daily-driver"):
        cmd = ["bash", loader_arg, "--profile", profile, "--print"]
        proc = subprocess.run(
            cmd,
            cwd=str(repo_root),
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            print(proc.stdout + proc.stderr, file=sys.stderr)
            return proc.returncode
        env: dict[str, str] = {}
        for line in proc.stdout.splitlines():
            if "=" not in line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip("'\"")
        if env.get("COG_PROFILE") != profile:
            print(f"profile mismatch: expected {profile}, got {env.get('COG_PROFILE')}", file=sys.stderr)
            return 1
        package_list = env.get("COG_PACKAGE_LIST", "")
        if not package_list or not Path(package_list).is_file():
            print(f"package list missing for {profile}: {package_list}", file=sys.stderr)
            return 1
        print(
            f"ok profile-loader {profile} init_mode={env.get('COG_INIT_MODE')} "
            f"systemd={env.get('COG_SYSTEMD_MODE')}"
        )

    validate = subprocess.run(
        [sys.executable, str(repo_root / "cog-os" / "forge" / "scripts" / "validate-profile.py"), "--mode", "fail"],
        cwd=str(repo_root),
        check=False,
    )
    if validate.returncode != 0:
        return validate.returncode
    print("forge profile loader tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
