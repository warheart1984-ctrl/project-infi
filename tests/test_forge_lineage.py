from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EMITTER = REPO_ROOT / "wolf-cog-os" / "scripts" / "emit-forge-lineage.py"
VALIDATOR = REPO_ROOT / "wolf-cog-os" / "scripts" / "validate-forge-lineage.py"
LINEAGE_LIB = REPO_ROOT / "wolf-cog-os" / "scripts" / "lib" / "forge_lineage.py"


def _load_lineage_lib():
    spec = importlib.util.spec_from_file_location("forge_lineage", LINEAGE_LIB)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ForgeLineageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fl = _load_lineage_lib()

    def test_lineage_id_is_stable(self) -> None:
        record = self.fl.build_lineage_record(
            pipeline_name="daily-driver",
            variant_id="daily-driver-main",
            profile_id="forge-selfhosted",
            reproducibility_seed="daily-driver-v1",
            package_sets=["base", "daily-driver"],
        )
        again = self.fl.build_lineage_record(
            pipeline_name="daily-driver",
            variant_id="daily-driver-main",
            profile_id="forge-selfhosted",
            reproducibility_seed="daily-driver-v1",
            package_sets=["daily-driver", "base"],
        )
        self.assertEqual(record["lineage_id"], again["lineage_id"])

    def test_emit_and_validate_roundtrip(self) -> None:
        out = REPO_ROOT / "ci-artifacts" / "test-forge-lineage.json"
        emit = subprocess.run(
            [
                sys.executable,
                str(EMITTER),
                "--pipeline",
                "wolf-cog-os/forge/pipelines/daily-driver.yaml",
                "--output",
                str(out.relative_to(REPO_ROOT)),
            ],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(emit.returncode, 0, msg=emit.stdout + emit.stderr)
        validate = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--lineage",
                str(out.relative_to(REPO_ROOT)),
                "--mode",
                "fail",
            ],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(validate.returncode, 0, msg=validate.stdout + validate.stderr)
        payload = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "forge-lineage.v1")


if __name__ == "__main__":
    unittest.main()
