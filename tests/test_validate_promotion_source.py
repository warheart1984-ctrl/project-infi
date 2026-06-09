from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / ".github" / "scripts" / "validate-promotion-source.py"


class ValidatePromotionSourceTests(unittest.TestCase):
    def _run(
        self,
        artifacts_dir: Path,
        source_run_id: str,
        expected_profile_id: str = "",
        required_scenarios: str = "",
    ) -> subprocess.CompletedProcess[str]:
        output_path = artifacts_dir / "promotion-source-validation.json"
        cmd = [
            sys.executable,
            str(VALIDATOR),
            "--artifacts-dir",
            str(artifacts_dir),
            "--source-run-id",
            source_run_id,
            "--output",
            str(output_path),
        ]
        if expected_profile_id:
            cmd.extend(["--expected-profile-id", expected_profile_id])
        if required_scenarios:
            cmd.extend(["--required-scenarios", required_scenarios])
        return subprocess.run(cmd, check=False, text=True, capture_output=True)

    def test_passes_when_source_run_id_matches(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            artifacts_dir = Path(td)
            (artifacts_dir / "build-metadata.json").write_text(
                json.dumps({"run": {"run_id": "12345"}}),
                encoding="utf-8",
            )
            result = self._run(artifacts_dir, "12345")
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            payload = json.loads((artifacts_dir / "promotion-source-validation.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "pass")

    def test_fails_when_source_run_id_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            artifacts_dir = Path(td)
            (artifacts_dir / "build-metadata.json").write_text(
                json.dumps({"run": {"run_id": "111"}}),
                encoding="utf-8",
            )
            result = self._run(artifacts_dir, "222")
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("source_run_id mismatch", result.stdout)

    def test_forge_profile_check_requires_matching_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            artifacts_dir = Path(td)
            (artifacts_dir / "build-metadata.json").write_text(
                json.dumps({"run": {"run_id": "42"}}),
                encoding="utf-8",
            )
            (artifacts_dir / "profile-attestation.json").write_text(
                json.dumps(
                    {
                        "profile": {"id": "forge-dev"},
                        "resolution": {"profile_id": "forge-dev"},
                    }
                ),
                encoding="utf-8",
            )
            (artifacts_dir / "profile-validation.json").write_text(
                json.dumps({"status": "pass"}),
                encoding="utf-8",
            )
            result = self._run(artifacts_dir, "42", expected_profile_id="forge-selfhosted")
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("profile mismatch", result.stdout)

    def test_required_scenarios_must_exist_and_pass(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            artifacts_dir = Path(td)
            (artifacts_dir / "build-metadata.json").write_text(
                json.dumps({"run": {"run_id": "99"}}),
                encoding="utf-8",
            )
            (artifacts_dir / "matrix-summary.json").write_text(
                json.dumps(
                    {
                        "scenarios": [
                            {"scenario_id": "1", "status": "passed"},
                            {"scenario_id": "3", "status": "failed"},
                            {"scenario_id": "6", "status": "passed"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = self._run(artifacts_dir, "99", required_scenarios="1,3,4,6")
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("required scenarios missing", result.stdout)
            self.assertIn("required scenarios not passed", result.stdout)

    def test_forge_build_state_required_when_profile_expected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            artifacts_dir = Path(td)
            (artifacts_dir / "build-metadata.json").write_text(
                json.dumps({"run": {"run_id": "77"}}),
                encoding="utf-8",
            )
            (artifacts_dir / "profile-attestation.json").write_text(
                json.dumps(
                    {
                        "profile": {"id": "forge-selfhosted"},
                        "resolution": {"profile_id": "forge-selfhosted"},
                    }
                ),
                encoding="utf-8",
            )
            (artifacts_dir / "profile-validation.json").write_text(
                json.dumps({"status": "pass"}),
                encoding="utf-8",
            )
            (artifacts_dir / "matrix-summary.json").write_text(
                json.dumps(
                    {
                        "scenarios": [
                            {"scenario_id": "1", "status": "passed"},
                            {"scenario_id": "3", "status": "passed"},
                            {"scenario_id": "4", "status": "passed"},
                            {"scenario_id": "6", "status": "passed"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = self._run(artifacts_dir, "77", expected_profile_id="forge-selfhosted", required_scenarios="1,3,4,6")
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("forge-build-state.json is missing", result.stdout)

    def test_forge_fixture_passes_full_promotion_validation(self) -> None:
        fixture_dir = REPO_ROOT / "cog-os" / "scripts" / "test" / "fixtures" / "promotion-forge-rc"
        legacy = REPO_ROOT / "wolf-cog-os" / "scripts" / "test" / "fixtures" / "promotion-forge-rc"
        if not fixture_dir.is_dir() and legacy.is_dir():
            fixture_dir = legacy
        if not fixture_dir.is_dir():
            self.skipTest("promotion fixture directory missing")
        result = self._run(
            fixture_dir,
            "424242",
            expected_profile_id="forge-selfhosted",
            required_scenarios="1,3,4,6",
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
