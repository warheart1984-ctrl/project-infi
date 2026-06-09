"""Tests for UGR trust bundle organ."""

import json
import unittest
from pathlib import Path

from src.ugr.trust_bundle.evidence import BUNDLE_ID
from src.ugr.trust_bundle.organ import TrustBundleOrgan
from src.ugr.trust_bundle.scenarios import (
    scenario_causal_rebuild,
    scenario_llm_execution_smoke,
    scenario_mesh_parity,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class TestTrustBundleScenarios(unittest.TestCase):
    def test_causal_rebuild_scenario(self):
        import tempfile

        with tempfile.TemporaryDirectory(prefix="ugr-trust-causal-") as temp:
            evidence = scenario_causal_rebuild(machine_id="machine-a", runtime_root=Path(temp))
            self.assertEqual(evidence.status, "pass")
            self.assertTrue(evidence.payload_sha256)

    def test_llm_execution_smoke_scenario(self):
        import tempfile

        with tempfile.TemporaryDirectory(prefix="ugr-trust-llm-") as temp:
            evidence = scenario_llm_execution_smoke(machine_id="machine-a", runtime_root=Path(temp))
            self.assertEqual(evidence.status, "pass")
            self.assertEqual(evidence.details.get("execution_status"), "EXECUTED")


class TestTrustBundleOrgan(unittest.TestCase):
    def test_organ_emits_proof_bundle_with_cross_profile_parity(self):
        import tempfile

        with tempfile.TemporaryDirectory(prefix="ugr-trust-organ-") as temp:
            output = Path(temp) / "bundle"
            organ = TrustBundleOrgan(output_dir=output, scenarios=("causal_rebuild", "llm_execution_smoke"))
            bundle = organ.run()
            self.assertEqual(bundle.get("bundle_id"), BUNDLE_ID)
            proof_path = Path(bundle["proof_bundle_path"])
            self.assertTrue(proof_path.exists())
            payload = json.loads(proof_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("overall_status"), "pass")
            parity = payload.get("cross_profile_parity") or {}
            self.assertTrue(all(item.get("matched") for item in parity.values()))

    def test_mesh_parity_scenario(self):
        import tempfile

        with tempfile.TemporaryDirectory(prefix="ugr-trust-mesh-") as temp:
            evidence = scenario_mesh_parity(machine_id="machine-a", runtime_root=Path(temp))
            self.assertEqual(evidence.status, "pass")


class TestTrustBundleManifestGate(unittest.TestCase):
    def test_manifest_validator_retired_with_wolf_forge(self):
        from src.ugr.trust_bundle.scenarios import scenario_gate_manifest

        evidence = scenario_gate_manifest(machine_id="machine-a")
        self.assertEqual(evidence.status, "pass")
        self.assertTrue(evidence.details.get("retired"))


if __name__ == "__main__":
    unittest.main()
