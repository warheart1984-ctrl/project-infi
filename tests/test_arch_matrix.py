from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "wolf-cog-os" / "scripts" / "validate-arch-matrix.py"


class ArchMatrixTests(unittest.TestCase):
    def test_arch_matrix_passes(self) -> None:
        cmd = [sys.executable, str(VALIDATOR), "--mode", "fail"]
        result = subprocess.run(cmd, cwd=str(REPO_ROOT), text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
