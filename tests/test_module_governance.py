"""Tests for the AAIS module governance protocol."""

from pathlib import Path
import shutil
import tempfile
import unittest

from src.governance_layer import GovernanceLayer
from src.immune_system import ImmuneSystemController
from src.module_governance import ModuleGovernanceController
from src.seam_log import list_seam_events


def _safe_module_spec(module_id: str = "signal_hud") -> dict:
    return {
        "module_id": module_id,
        "label": "Signal HUD",
        "lane": "experience",
        "declared_scope": ["ui", "telemetry"],
        "cisiv": {
            "concept": {
                "status": "passed",
                "summary": "Provide a transient HUD for operator-visible telemetry signals.",
            },
            "identity": {
                "status": "passed",
                "summary": "Never reconstruct or persist user identity.",
            },
            "structure": {
                "status": "passed",
                "summary": "Stay inside the UI and telemetry surfaces under Jarvis routing.",
            },
            "implementation": {
                "status": "implemented",
                "summary": "The module is implemented as a bounded UI telemetry surface.",
            },
            "verification": {
                "status": "verified",
                "summary": "Governance admission and runtime smoke checks were recorded.",
                "evidence": [
                    "pytest tests/test_module_governance.py -q",
                    "module admission smoke",
                ],
            },
        },
        "compliance": {
            "stores_persistent_user_metadata": False,
            "creates_user_identity_profiles": False,
            "retains_behavioral_history": False,
            "infers_user_labels": False,
            "builds_personality_models": False,
            "builds_behavior_models": False,
            "stores_live_signals": False,
            "reconstructs_signals": False,
            "requires_identity_history": False,
            "adaptive_logic_scope": "system",
            "alters_nova_tone": False,
            "alters_nova_role": False,
            "alters_nova_constancy": False,
            "bypasses_jarvis_authority": False,
            "bypasses_routing": False,
            "logs_user_identity": False,
            "logs_behavior_patterns": False,
            "logs_biometric_traces": False,
            "hidden_logging": False,
            "exfiltrates_data": False,
        },
    }


class TestModuleGovernanceController(unittest.TestCase):
    """Verify admission, rejection, and runtime immune responses."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="module-governance-"))
        self.immune = ImmuneSystemController(runtime_dir=self.temp_dir)
        self.governance = GovernanceLayer(runtime_dir=self.temp_dir)
        self.controller = ModuleGovernanceController(
            runtime_dir=self.temp_dir,
            immune_controller=self.immune,
            governance_controller=self.governance,
        )
        self.immune.reset()
        self.governance.reset()
        self.controller.reset()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_admit_module_accepts_compliant_spec(self):
        result = self.controller.admit_module(_safe_module_spec())

        self.assertTrue(result["installable"])
        self.assertEqual(result["module"]["status"], "admitted")
        self.assertEqual(result["module"]["cisiv_status"], "pass")
        self.assertEqual(result["module"]["cisiv_stage"], "verification")
        self.assertTrue(all(check["passed"] for check in result["evaluation"]["checks"]))

    def test_admit_module_rejects_persistent_user_data(self):
        spec = _safe_module_spec("profile_mirror")
        spec["compliance"]["stores_persistent_user_metadata"] = True

        result = self.controller.admit_module(spec)

        self.assertFalse(result["installable"])
        self.assertEqual(result["module"]["status"], "rejected")
        self.assertIn("persistent user metadata", " ".join(result["evaluation"]["violations"]).lower())

    def test_admit_module_rejects_missing_verification_evidence(self):
        spec = _safe_module_spec("unverified_module")
        spec["cisiv"]["verification"]["evidence"] = []

        result = self.controller.admit_module(spec)

        self.assertFalse(result["installable"])
        self.assertEqual(result["module"]["status"], "rejected")
        self.assertIn("verification evidence is required", " ".join(result["evaluation"]["violations"]).lower())

    def test_runtime_signal_blacklists_hostile_module(self):
        self.controller.admit_module(_safe_module_spec("tone_spoofer"))

        result = self.controller.report_runtime_signal(
            "tone_spoofer",
            signal_type="nova_identity_interference",
            reason="Module attempted to alter Nova's tone.",
        )

        self.assertEqual(result["module"]["status"], "blacklisted")
        immune_snapshot = self.immune.snapshot(limit_events=6, limit_incidents=6)
        self.assertTrue(any(item["module_id"] == "tone_spoofer" for item in immune_snapshot["quarantined_modules"]))
        self.assertTrue(any(item["module_id"] == "tone_spoofer" for item in immune_snapshot["blacklisted_modules"]))
        seam_events = list_seam_events(runtime_dir=self.temp_dir, limit=10)
        self.assertTrue(any(item["component_id"] == "tone_spoofer" for item in seam_events))
        self.assertTrue(any(item["classification"] == "boundary_violation" for item in seam_events))
