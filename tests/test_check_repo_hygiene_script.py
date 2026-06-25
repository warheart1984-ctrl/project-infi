from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class RepoHygieneScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="repo-hygiene-script-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        repo = Path(__file__).resolve().parents[1]
        for rel in (
            ".github/scripts/check-repo-hygiene.py",
            ".github/scripts/validate-repo-hygiene-manifest.py",
            "docs/audit/REPO_HYGIENE_MANIFEST.json",
            "schemas/repo_hygiene_manifest.v1.json",
        ):
            src = repo / rel
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    def _run(self, *extra: str) -> subprocess.CompletedProcess[str]:
        cmd = [
            "python",
            ".github/scripts/check-repo-hygiene.py",
            "--skip-bundle-compare",
            *extra,
        ]
        return subprocess.run(cmd, cwd=self.root, text=True, capture_output=True, check=False)

    def _run_validator(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python", ".github/scripts/validate-repo-hygiene-manifest.py", "--mode", "fail"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_manifest_validator_passes(self) -> None:
        result = self._run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_clean_repo_passes(self) -> None:
        result = self._run("--mode", "fail")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("errors=0", result.stdout)

    def test_rule_forbidden_root_name(self) -> None:
        (self.root / "AAIS-main").mkdir()
        result = self._run("--mode", "fail")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("hygiene.forbidden_root_name", result.stdout)

    def test_rule_forbidden_root_glob(self) -> None:
        (self.root / "test.iso").write_text("x", encoding="utf-8")
        result = self._run("--mode", "warn")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("hygiene.forbidden_root_glob", result.stdout)

    def test_rule_poison_dir(self) -> None:
        mirror = self.root / "accidental-bundle"
        (mirror / "opt" / "cogos").mkdir(parents=True)
        result = self._run("--mode", "fail")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("hygiene.poison_dir", result.stdout)

    def test_rule_local_work_dir(self) -> None:
        (self.root / "ci-artifacts").mkdir()
        result = self._run("--mode", "warn")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("hygiene.local_work_dir", result.stdout)

    def test_rule_stray_root_argv(self) -> None:
        (self.root / "--broken-arg").write_text("x", encoding="utf-8")
        result = self._run("--mode", "warn")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("hygiene.stray_root_argv", result.stdout)

    def test_warn_mode_exits_zero_on_error(self) -> None:
        (self.root / "AAIS-main").mkdir()
        result = self._run("--mode", "warn")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("hygiene.forbidden_root_name", result.stdout)

    def test_writes_json_report_with_remediation(self) -> None:
        (self.root / "AAIS-main").mkdir()
        out = self.root / "report.json"
        result = self._run("--output", str(out), "--mode", "warn")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(out.read_text(encoding="utf-8"))
        self.assertGreaterEqual(payload["violations"], 1)
        self.assertTrue(payload["findings"])
        self.assertTrue(payload["findings"][0].get("remediation_hint"))


if __name__ == "__main__":
    unittest.main()
