from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "wolf-cog-os" / "scripts" / "validate-cloud-output.py"


class CloudOutputTests(unittest.TestCase):
    def test_raw_img_registry_only_passes(self) -> None:
        cmd = [sys.executable, str(VALIDATOR), "--format", "raw-img", "--registry-only", "--mode", "fail"]
        result = subprocess.run(cmd, cwd=str(REPO_ROOT), text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_raw_img_module_exists(self) -> None:
        module = REPO_ROOT / "wolf-cog-os" / "scripts" / "lib" / "outputs" / "raw-img.sh"
        self.assertTrue(module.is_file())
        text = module.read_text(encoding="utf-8")
        self.assertNotIn("not implemented yet", text)

    def test_qcow2_module_exists(self) -> None:
        module = REPO_ROOT / "wolf-cog-os" / "scripts" / "lib" / "outputs" / "qcow2.sh"
        self.assertTrue(module.is_file())
        text = module.read_text(encoding="utf-8")
        self.assertNotIn("not implemented yet", text)


if __name__ == "__main__":
    unittest.main()
