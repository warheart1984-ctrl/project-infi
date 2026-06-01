from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATE_PROFILE = REPO_ROOT / "wolf-cog-os" / "scripts" / "validate-profile.py"
EMIT_ATTESTATION = REPO_ROOT / "wolf-cog-os" / "scripts" / "emit-profile-attestation.py"
VALIDATE_LEDGER = REPO_ROOT / ".github" / "scripts" / "validate-governance-ledger.py"
PROFILE_LOADER = REPO_ROOT / "wolf-cog-os" / "scripts" / "lib" / "profile-loader.sh"


def _run(cmd: list[str], cwd: Path, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(cmd, cwd=cwd, env=merged_env, check=False, text=True, capture_output=True)


class TestProfileLoaderPrecedenceEdgeCases(unittest.TestCase):
    def _resolve_profile(self, env_overrides: Dict[str, str], cli_profile: str = "") -> str:
        cli_arg = cli_profile.replace("'", "'\"'\"'")
        setup_parts = [
            "unset COGOS_FORGE_PROFILE",
            "unset COGOS_BOOT_PROFILE",
        ]
        for key, value in env_overrides.items():
            escaped = value.replace("'", "'\"'\"'")
            setup_parts.append(f"export {key}='{escaped}'")
        setup_parts.append("source 'wolf-cog-os/scripts/lib/profile-loader.sh'")
        setup_parts.append(f"forge_resolve_profile_id '{cli_arg}'")
        script = "; ".join(setup_parts)
        env = os.environ.copy()
        env.pop("COGOS_FORGE_PROFILE", None)
        env.pop("COGOS_BOOT_PROFILE", None)
        result = subprocess.run(
            ["bash", "-lc", script],
            cwd=REPO_ROOT,
            env=env,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return result.stdout.strip()

    def test_non_forge_boot_profile_falls_back_to_default(self) -> None:
        resolved = self._resolve_profile({"COGOS_BOOT_PROFILE": "dev-desktop"})
        self.assertEqual(resolved, "forge-selfhosted")

    def test_forge_env_beats_boot_profile(self) -> None:
        resolved = self._resolve_profile(
            {
                "COGOS_FORGE_PROFILE": "forge-canary",
                "COGOS_BOOT_PROFILE": "forge-selfhosted",
            }
        )
        self.assertEqual(resolved, "forge-canary")

    def test_cli_beats_all_environment_inputs(self) -> None:
        resolved = self._resolve_profile(
            {
                "COGOS_FORGE_PROFILE": "forge-canary",
                "COGOS_BOOT_PROFILE": "forge-selfhosted",
            },
            cli_profile="forge-dev",
        )
        self.assertEqual(resolved, "forge-dev")


class TestValidateProfileEdgeCases(unittest.TestCase):
    def _write_schema(self, root: Path) -> Path:
        schema_path = root / "schema.json"
        schema_path.write_text(
            json.dumps({"required_top_level": ["schema_version", "profile_id"]}),
            encoding="utf-8",
        )
        return schema_path

    def test_missing_profile_warn_mode_reports_warning_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            schema_path = self._write_schema(root)
            output_path = root / "profile-validation.json"
            profiles_root = root / "profiles"
            profiles_root.mkdir(parents=True, exist_ok=True)

            result = _run(
                [
                    sys.executable,
                    str(VALIDATE_PROFILE),
                    "--profile",
                    "does-not-exist",
                    "--profiles-root",
                    str(profiles_root),
                    "--schema",
                    str(schema_path),
                    "--mode",
                    "warn",
                    "--output",
                    str(output_path),
                ],
                cwd=root,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "pass")
            self.assertTrue(any("Profile file not found" in f["message"] for f in payload["findings"]))

    def test_missing_profile_fail_mode_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            schema_path = self._write_schema(root)
            output_path = root / "profile-validation.json"
            profiles_root = root / "profiles"
            profiles_root.mkdir(parents=True, exist_ok=True)

            result = _run(
                [
                    sys.executable,
                    str(VALIDATE_PROFILE),
                    "--profile",
                    "missing-profile",
                    "--profiles-root",
                    str(profiles_root),
                    "--schema",
                    str(schema_path),
                    "--mode",
                    "fail",
                    "--output",
                    str(output_path),
                ],
                cwd=root,
            )
            self.assertEqual(result.returncode, 1, msg=result.stderr)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "fail")


class TestGovernanceLedgerMappingIntegrity(unittest.TestCase):
    def test_missing_make_target_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "Makefile").write_text("rootfs:\n\t@echo ok\n", encoding="utf-8")
            (root / "consumer.yml").write_text("run: make rootfs\n", encoding="utf-8")
            ledger = {
                "default_verification_policy": "warn",
                "commands": [
                    {
                        "id": "make.missing-target",
                        "owner": "Makefile",
                        "component": "ci",
                        "invocation": {"type": "make_target", "makefile": "Makefile", "target": "iso-tree"},
                        "required_env": [],
                        "optional_env": [],
                        "deprecation": {"status": "active", "replacement": ""},
                        "verification_policy": "warn",
                        "consumers": [{"path": "consumer.yml", "contains": "make rootfs"}],
                    }
                ],
            }
            ledger_path = root / "command-ledger.json"
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")

            result = _run(
                [sys.executable, str(VALIDATE_LEDGER), "--ledger", str(ledger_path), "--mode", "fail"],
                cwd=root,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("Target 'iso-tree' not found", result.stdout)


class TestAttestationArtifactBehavior(unittest.TestCase):
    def test_dry_run_sets_not_applicable_binding_status(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            profiles_root = root / "profiles"
            profiles_root.mkdir(parents=True, exist_ok=True)
            (profiles_root / "forge-selfhosted.yaml").write_text("profile_id: forge-selfhosted\n", encoding="utf-8")

            output_path = root / "profile-attestation.json"
            result = _run(
                [
                    sys.executable,
                    str(EMIT_ATTESTATION),
                    "--profile",
                    "forge-selfhosted",
                    "--profiles-root",
                    str(profiles_root),
                    "--output",
                    str(output_path),
                    "--dry-run",
                ],
                cwd=root,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["artifact_binding"]["binding_status"], "not-applicable-dry-run")

    def test_iso_and_manifest_generate_bound_status(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            profiles_root = root / "profiles"
            profiles_root.mkdir(parents=True, exist_ok=True)
            (profiles_root / "forge-selfhosted.yaml").write_text("profile_id: forge-selfhosted\n", encoding="utf-8")
            iso_path = root / "artifact.iso"
            manifest_path = root / "manifest.json"
            iso_path.write_bytes(b"fake iso bytes")
            manifest_path.write_text("{}", encoding="utf-8")

            output_path = root / "profile-attestation.json"
            result = _run(
                [
                    sys.executable,
                    str(EMIT_ATTESTATION),
                    "--profile",
                    "forge-selfhosted",
                    "--profiles-root",
                    str(profiles_root),
                    "--output",
                    str(output_path),
                    "--iso-path",
                    str(iso_path),
                    "--manifest-path",
                    str(manifest_path),
                ],
                cwd=root,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["artifact_binding"]["binding_status"], "bound")
            self.assertTrue(payload["artifact_binding"]["iso_sha256"])
            self.assertTrue(payload["artifact_binding"]["manifest_sha256"])
