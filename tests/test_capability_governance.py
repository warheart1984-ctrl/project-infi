"""Tests for Nova Cortex lobe capability governance."""

import unittest

from src.cog_runtime import nova_cortex_spec, validate_nova_cortex_capability_governance
from src.cog_runtime.capability_governance import (
    CORTEX_MODULE_CAPABILITY_MATRIX,
    NOVA_LOBE_CAPABILITY_MATRIX,
    lobe_capability_contract,
    validate_cortex_module_capability_matrix,
    validate_runtime_capability_spec,
)


class TestCapabilityGovernance(unittest.TestCase):
    def test_matrix_covers_all_family_runtimes(self):
        spec = nova_cortex_spec()
        result = validate_nova_cortex_capability_governance(spec)
        self.assertTrue(result["valid"], msg=result["issues"])
        self.assertEqual(result["runtime_count"], len(NOVA_LOBE_CAPABILITY_MATRIX))

    def test_every_runtime_has_capability_fields(self):
        spec = nova_cortex_spec()
        for runtime in spec["runtimes"]:
            validation = validate_runtime_capability_spec(runtime)
            self.assertTrue(validation["valid"], msg=f"{runtime.get('id')}: {validation['issues']}")

    def test_cortex_modules_have_capability_matrix(self):
        result = validate_cortex_module_capability_matrix()
        self.assertTrue(result["valid"], msg=result["issues"])
        self.assertIn("cortex.arcs", CORTEX_MODULE_CAPABILITY_MATRIX)
        self.assertIn("cortex.tuning", CORTEX_MODULE_CAPABILITY_MATRIX)
        self.assertIn("nova.narrative", CORTEX_MODULE_CAPABILITY_MATRIX)

    def test_lobe_contract_matches_matrix(self):
        contract = lobe_capability_contract("cognitive.attention")
        self.assertEqual(contract["evidence_status"], NOVA_LOBE_CAPABILITY_MATRIX["cognitive.attention"]["evidence_status"])
        self.assertIn("focus_artifact", contract["capability_metric"])

    def test_drift_detects_spec_matrix_mismatch(self):
        runtime = dict(nova_cortex_spec()["runtimes"][0])
        runtime["capability_metric"] = "too short"
        validation = validate_runtime_capability_spec(runtime)
        self.assertFalse(validation["valid"])


if __name__ == "__main__":
    unittest.main()
