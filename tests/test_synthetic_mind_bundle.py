from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_PY = REPO_ROOT / "scripts" / "cogos" / "build_synthetic_mind_bundle.py"
BUNDLE_DIR = REPO_ROOT / "artifacts" / "synthetic-mind-bundle-test"


class SyntheticMindBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if BUNDLE_DIR.exists():
            import shutil

            shutil.rmtree(BUNDLE_DIR)
        result = subprocess.run(
            [sys.executable, str(BUILD_PY), str(BUNDLE_DIR)],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stdout + result.stderr)

    def test_manifest_present(self) -> None:
        manifest_path = BUNDLE_DIR / "synthetic_mind_manifest.json"
        self.assertTrue(manifest_path.is_file())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["bundle_version"], "synthetic_mind_bundle.v1")
        self.assertEqual(manifest["family_id"], "nova.cortex")
        self.assertEqual(manifest["spark_pipeline_id"], "nova.spark.v1")

    def test_spark_modules_present(self) -> None:
        src_root = BUNDLE_DIR / "opt" / "cogos" / "runtime" / "src"
        for rel in (
            "cog_runtime/coherence_projection.py",
            "cog_runtime/spark_pipeline.py",
            "cog_runtime/formal/spine_pipeline.py",
        ):
            self.assertTrue((src_root / rel).is_file(), msg=rel)

    def test_bridge_importable(self) -> None:
        runtime_root = BUNDLE_DIR / "opt" / "cogos" / "runtime"
        src_root = runtime_root / "src"
        code = """
from src.cogos_runtime_bridge import family_spec
spec = family_spec()
assert spec["family_id"] == "nova.cortex"
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(REPO_ROOT),
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": f"{runtime_root}{__import__('os').pathsep}{src_root}",
            },
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)


if __name__ == "__main__":
    unittest.main()
