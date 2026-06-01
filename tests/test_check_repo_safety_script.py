from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
import unittest


class RepoSafetyScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="repo-safety-script-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        script_src = Path("E:/project-infi/.github/scripts/check-repo-safety.py")
        script_dst = self.root / ".github/scripts/check-repo-safety.py"
        script_dst.parent.mkdir(parents=True, exist_ok=True)
        script_dst.write_text(script_src.read_text(encoding="utf-8"), encoding="utf-8")

    def _run(self, *paths: str) -> subprocess.CompletedProcess[str]:
        cmd = ["python", ".github/scripts/check-repo-safety.py"]
        for path in paths:
            cmd.extend(["--path", path])
        return subprocess.run(cmd, cwd=self.root, text=True, capture_output=True, check=False)

    def test_allows_scoped_rm_rf(self) -> None:
        script = self.root / "scripts/safe.sh"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text('rm -rf "$TMPDIR/build"\n', encoding="utf-8")

        result = self._run("scripts")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("violations=0", result.stdout)

    def test_flags_git_clean_force(self) -> None:
        workflow = self.root / ".github/workflows/bad.yml"
        workflow.parent.mkdir(parents=True, exist_ok=True)
        workflow.write_text("run: git clean -fdx\n", encoding="utf-8")

        result = self._run(".github/workflows")

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("repo_safety.git_clean", result.stdout)

    def test_flags_rm_rf_root(self) -> None:
        script = self.root / "scripts/bad.sh"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("rm -rf /\n", encoding="utf-8")

        result = self._run("scripts")

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("repo_safety.rm_rf_root", result.stdout)

    def test_allows_explicit_inline_waiver(self) -> None:
        script = self.root / "scripts/waived.sh"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("git clean -fdx # repo-safety: allow\n", encoding="utf-8")

        result = self._run("scripts")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("violations=0", result.stdout)


if __name__ == "__main__":
    unittest.main()
