from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INVARIANTS = REPO_ROOT / "wolf-cog-os" / "scripts" / "validate-substrate-invariants.py"
REPLAY_VALIDATOR = REPO_ROOT / "wolf-cog-os" / "scripts" / "validate-replay-adapter.py"
BACKEND_VALIDATOR = REPO_ROOT / "wolf-cog-os" / "scripts" / "validate-rootfs-backend.py"
PIPELINE_VALIDATOR = REPO_ROOT / "wolf-cog-os" / "scripts" / "validate-pipeline.py"


class UniversalSubstrateTests(unittest.TestCase):
    def test_invariants_registry_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(INVARIANTS), "--mode", "fail"],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_universal_replay_modules_exist(self) -> None:
        adapter_dir = REPO_ROOT / "wolf-cog-os" / "scripts" / "lib" / "replay-adapters"
        for name in ("windows-wim-layout", "macos-apfs-layout", "android-super-layout"):
            self.assertTrue((adapter_dir / f"{name}.sh").is_file(), msg=name)

    def test_universal_backend_modules_exist(self) -> None:
        backend_dir = REPO_ROOT / "wolf-cog-os" / "scripts" / "lib" / "backends"
        for name in ("winpe-backend", "darwin-backend", "android-backend"):
            self.assertTrue((backend_dir / f"{name}.sh").is_file(), msg=name)

    def test_substrate_registry_includes_universal_classes(self) -> None:
        registry = json.loads(
            (REPO_ROOT / "wolf-cog-os" / "forge" / "substrates" / "registry.json").read_text(encoding="utf-8")
        )
        for substrate_id in ("windows-installer", "macos-installer", "android-bootable"):
            self.assertIn(substrate_id, registry["substrates"])

    def test_universal_pipelines_validate(self) -> None:
        for pipeline in (
            "wolf-cog-os/forge/pipelines/windows-installer.yaml",
            "wolf-cog-os/forge/pipelines/macos-installer.yaml",
            "wolf-cog-os/forge/pipelines/android-system.yaml",
        ):
            result = subprocess.run(
                [sys.executable, str(PIPELINE_VALIDATOR), pipeline, "--mode", "fail"],
                cwd=str(REPO_ROOT),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=pipeline + ": " + result.stdout + result.stderr)

    def test_inject_backends_registry_only(self) -> None:
        for backend in ("winpe-backend", "darwin-backend", "android-backend"):
            result = subprocess.run(
                [
                    sys.executable,
                    str(BACKEND_VALIDATOR),
                    "--backend",
                    backend,
                    "--registry-only",
                    "--mode",
                    "fail",
                ],
                cwd=str(REPO_ROOT),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=backend + ": " + result.stdout + result.stderr)

    def test_replay_registry_includes_universal_adapters(self) -> None:
        result = subprocess.run(
            [sys.executable, str(REPLAY_VALIDATOR), "--mode", "fail"],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
