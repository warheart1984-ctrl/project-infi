"""Tests for unified contribution discovery framework."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.discovery.contribution_discovery import ContributionDiscoveryService
from src.ugr.discovery.contribution_spec import ContributionSpec, contribution_id_from_spec
from src.ugr.discovery.contribution_validity import validate_contribution_spec
from src.ugr.discovery.validators.workflow import validate_workflow_contribution


class TestContributionDiscovery(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-contrib-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "test-contrib-key"
        os.environ["UGR_SUBSYSTEM_DISCOVERY_ENABLED"] = "1"
        os.environ["UGR_REWARDS_SHADOW_ONLY"] = "1"

    def tearDown(self):
        for key in ("AAIS_RUNTIME_DIR", "URG_RECEIPT_SIGNING_KEY", "UGR_SUBSYSTEM_DISCOVERY_ENABLED", "UGR_REWARDS_SHADOW_ONLY"):
            os.environ.pop(key, None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_workflow_validator_passes(self):
        result = validate_workflow_contribution(
            {
                "workflow_id": "wf-demo",
                "run_id": "wfr_abc123",
                "step_count": 3,
                "dry_run": False,
            },
            tenant_id="tenant:acme",
            operator_id="op-1",
            aais_instance_id="aais-local",
        )
        self.assertTrue(result.valid)

    def test_contribution_id_stable(self):
        spec = ContributionSpec(
            contribution_type="workflow",
            payload={"workflow_id": "wf-demo", "run_id": "wfr_abc", "step_count": 2},
        )
        cid = contribution_id_from_spec(spec)
        self.assertEqual(len(cid), 64)
        self.assertEqual(cid, spec.contribution_id())

    def test_discover_workflow_contribution(self):
        service = ContributionDiscoveryService(runtime_dir=str(self.temp_root))
        result = service.discover(
            {
                "tenant_id": "tenant:acme",
                "operator_id": "op-1",
                "aais_instance_id": "aais-local",
                "contribution_type": "workflow",
                "payload": {
                    "workflow_id": "wf-demo",
                    "run_id": "wfr_abc123",
                    "step_count": 2,
                    "dry_run": False,
                },
            }
        )
        self.assertEqual(result.get("status"), "discovered")
        self.assertEqual(result.get("contribution_type"), "workflow")
        receipt = result.get("contribution_discovery_receipt") or {}
        self.assertTrue(receipt.get("receipt_sig"))

    def test_invariant_validator_requires_digest(self):
        spec = ContributionSpec(
            contribution_type="invariant",
            payload={"mission_id": "mid-1", "all_passed": True},
        )
        result = validate_contribution_spec(
            spec,
            tenant_id="tenant:acme",
            operator_id="op-1",
            aais_instance_id="aais-local",
        )
        self.assertFalse(result.valid)


if __name__ == "__main__":
    unittest.main()
