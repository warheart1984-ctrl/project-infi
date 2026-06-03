"""Tests for governed provider marketplace (Phase 3)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.ugr.mission.marketplace import apply_provider_organ_mutation, query_organs
from src.ugr.mission.mission_runtime import UGRMissionRuntime
from src.ugr.mission.organ_trust import (
    TRUST_SHADOW_THRESHOLD,
    organ_requires_shadow,
    resolve_execution_mode_for_organ,
)
from src.ugr.mission.execution_policy import EXECUTION_MODE_LIVE, EXECUTION_MODE_SHADOW
from src.ugr.mission.provider_organ import ORGAN_STATUS_ADMITTED, ProviderOrganRegistry


class TestMarketplaceQuery(unittest.TestCase):
    def test_query_organs_acme(self):
        catalog = query_organs(tenant_id="tenant:acme")
        self.assertEqual(catalog["tenant_id"], "tenant:acme")
        self.assertGreaterEqual(catalog["organ_count"], 1)
        self.assertTrue(all("organ_id" in o for o in catalog["organs"]))


class TestMarketplaceGovernance(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-mkt-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "mkt-test-op"
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "mkt-test-urg"
        os.environ["URG_GOVERNANCE_OPERATOR_ALLOWLIST"] = "governance-operator"
        os.environ["URG_GOVERNANCE_APPLY"] = "1"

    def tearDown(self):
        for key in (
            "URG_OPERATOR_RECEIPT_KEY",
            "URG_RECEIPT_SIGNING_KEY",
            "URG_GOVERNANCE_OPERATOR_ALLOWLIST",
            "URG_GOVERNANCE_APPLY",
        ):
            os.environ.pop(key, None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_organ_admit_via_governance(self):
        payload = {
            "mission_kind": "governance_mutation",
            "mutation_target": "provider_organs",
            "mutation_op": "organ_admit",
            "operator_id": "governance-operator",
            "tenant_id": "tenant:acme",
            "organ_spec": {
                "organ_id": "organ-test-admit",
                "tenant_scope": "tenant:acme",
                "status": "admitted",
                "identity": {
                    "organ_id": "organ-test-admit",
                    "tier": "tiny",
                    "label": "Test Admit Organ",
                },
                "envelope": {"proposal_only": True, "execution_backend": "local"},
                "function": {"capabilities": ["governed_super_router_demo"]},
                "contract": {
                    "provider": "local",
                    "max_cost_units": 1,
                    "allowed_regions": ["tenant-us"],
                    "allowed_domains": ["governed_super_router_demo"],
                    "admissible_rails": ["SAFE"],
                },
            },
            "aais_instance_id": "aais-primary",
            "region_id": "tenant-us",
            "steps": [{"step_id": "gov", "objective": "admit organ"}],
        }
        result = UGRMissionRuntime(runtime_dir=self.temp_root).run_mission(payload)
        self.assertEqual(result["status"], "ok")
        registry = ProviderOrganRegistry(tenant_id="tenant:acme")
        self.assertIsNotNone(registry.get("organ-test-admit"))

    def test_organ_suspend_blocks_auto_route(self):
        overlay_dir = Path(__file__).resolve().parents[1] / "deploy" / "ugr" / "tenants" / "tenant-acme"
        overlay_dir.mkdir(parents=True, exist_ok=True)
        suspended_path = overlay_dir / "provider-organs.json"
        backup = suspended_path.read_text(encoding="utf-8") if suspended_path.exists() else None
        try:
            suspended_path.write_text(
                json.dumps(
                    {
                        "organs": {
                            "organ-local-tiny": {
                                "tenant_scope": "global",
                                "status": "suspended",
                                "identity": {"organ_id": "organ-local-tiny", "tier": "tiny"},
                                "envelope": {"proposal_only": True},
                                "function": {},
                                "contract": {
                                    "provider": "local",
                                    "max_cost_units": 2,
                                    "allowed_regions": ["tenant-us"],
                                    "allowed_domains": ["governed_super_router_demo"],
                                },
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            registry = ProviderOrganRegistry(tenant_id="tenant:acme")
            self.assertEqual(registry.admitted_organ_ids().count("organ-local-tiny"), 0)
        finally:
            if backup is None:
                if suspended_path.exists():
                    suspended_path.unlink()
            else:
                suspended_path.write_text(backup, encoding="utf-8")


class TestTrustGates(unittest.TestCase):
    def test_low_trust_downgrades_live(self):
        mode = resolve_execution_mode_for_organ(EXECUTION_MODE_LIVE, TRUST_SHADOW_THRESHOLD - 0.1)
        self.assertEqual(mode, EXECUTION_MODE_SHADOW)

    def test_high_trust_keeps_live(self):
        mode = resolve_execution_mode_for_organ(EXECUTION_MODE_LIVE, 0.9)
        self.assertEqual(mode, EXECUTION_MODE_LIVE)

    def test_organ_requires_shadow(self):
        self.assertTrue(organ_requires_shadow(0.1))
        self.assertFalse(organ_requires_shadow(0.9))
