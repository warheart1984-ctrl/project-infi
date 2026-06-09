"""Tests for UGR Phase 4 platform scale."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.pattern_ledger import PatternLedgerStore
from src.ugr.platform.cognition_cicd import CognitionCICDPipeline
from src.ugr.platform.graph_shard import GraphShardRouter
from src.ugr.platform.shadow_runtime import ShadowRuntimeEvaluator, compare_deliberation_results
from src.ugr.platform.sharded_ledger import ShardedPatternLedger
from src.ugr.platform.tenant_registry import TenantRegistry, normalize_tenant_id
from src.ugr.unified_runtime import UnifiedGovernedRuntime


class TestTenantRegistry(unittest.TestCase):
    def test_normalize_tenant_id(self):
        self.assertEqual(normalize_tenant_id("default"), "global")
        self.assertEqual(normalize_tenant_id("acme"), "tenant:acme")

    def test_registry_loads_global(self):
        registry = TenantRegistry()
        global_tenant = registry.get("global")
        self.assertIsNotNone(global_tenant)
        self.assertTrue(global_tenant.enabled)


class TestShardedLedger(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-platform-"))
        self.tenants_path = self.temp_root / "tenants.json"
        self.shards_path = self.temp_root / "shards.json"
        self.tenants_path.write_text(
            json.dumps(
                {
                    "tenants": {
                        "global": {
                            "enabled": True,
                            "shard_id": "shard-global",
                            "overlay_global": False,
                        },
                        "tenant:acme": {
                            "enabled": True,
                            "shard_id": "shard-acme",
                            "overlay_global": True,
                        },
                        "tenant:contoso": {
                            "enabled": True,
                            "shard_id": "shard-contoso",
                            "overlay_global": True,
                        },
                    }
                }
            ),
            encoding="utf-8",
        )
        self.shards_path.write_text(
            json.dumps(
                {
                    "shards": {
                        "shard-global": {"domain": "global", "enabled": True},
                        "shard-acme": {"domain": "tenant", "enabled": True},
                        "shard-contoso": {"domain": "tenant", "enabled": True},
                    }
                }
            ),
            encoding="utf-8",
        )
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root / "runtime")
        os.environ["UGR_TENANTS_CONFIG"] = str(self.tenants_path)
        os.environ["UGR_GRAPH_SHARDS_CONFIG"] = str(self.shards_path)
        tenants = TenantRegistry(self.tenants_path)
        router = GraphShardRouter(shards_path=self.shards_path, tenants=tenants, runtime_root=self.temp_root / "runtime")
        self.ledger = ShardedPatternLedger(router=router, tenants=tenants)

    def tearDown(self):
        shutil.rmtree(self.temp_root, ignore_errors=True)
        for key in ("AAIS_RUNTIME_DIR", "UGR_TENANTS_CONFIG", "UGR_GRAPH_SHARDS_CONFIG", "UGR_PLATFORM_ENABLED"):
            os.environ.pop(key, None)

    def _claim(self, subject: str, tenant_scope: str) -> dict:
        return self.ledger.append_claim(
            {
                "claim_id": self.ledger.make_claim_id(subject, "describes", "topic", "test"),
                "subject": subject,
                "predicate": "describes",
                "object": "topic",
                "confidence": 0.9,
                "source_lane": "test",
                "evidence_refs": [],
                "tenant_scope": tenant_scope,
                "status": "accepted",
            }
        )

    def test_tenant_isolation(self):
        self._claim("global-fact", "global")
        self._claim("acme-secret", "tenant:acme")
        self._claim("contoso-secret", "tenant:contoso")

        acme_rows = self.ledger.read_claims(tenant_scope="tenant:acme")
        acme_subjects = {row.get("subject") for row in acme_rows}
        self.assertIn("global-fact", acme_subjects)
        self.assertIn("acme-secret", acme_subjects)
        self.assertNotIn("contoso-secret", acme_subjects)

    def test_claims_route_to_shard_directories(self):
        record = self._claim("routed", "tenant:acme")
        shard_id = record.get("shard_id")
        self.assertEqual(shard_id, "shard-acme")
        shard_claims = self.temp_root / "runtime" / "collective-pattern-ledger" / "shards" / "shard-acme"
        self.assertTrue(shard_claims.exists())


class TestPatternLedgerPlatformSwitch(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-platform-switch-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["UGR_PLATFORM_ENABLED"] = "1"

    def tearDown(self):
        shutil.rmtree(self.temp_root, ignore_errors=True)
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        os.environ.pop("UGR_PLATFORM_ENABLED", None)

    def test_platform_enabled_uses_sharded_backend(self):
        store = PatternLedgerStore(runtime_dir=self.temp_root)
        self.assertTrue(store._platform)
        record = store.append_claim(
            {
                "claim_id": store.make_claim_id("platform", "enabled", "true", "test"),
                "subject": "platform",
                "predicate": "enabled",
                "object": "true",
                "confidence": 1.0,
                "source_lane": "test",
                "evidence_refs": [],
                "tenant_scope": "global",
                "status": "accepted",
            }
        )
        self.assertIn("shard_id", record)


class TestShadowRuntimeAndCICD(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-shadow-"))
        self.promotion_path = self.temp_root / "promotion.json"
        self.promotion_path.write_text(
            json.dumps({"promotion": {"min_belief_match_rate": 0.95, "require_status_match": True}}),
            encoding="utf-8",
        )
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root / "prod")
        os.environ["UGR_COGNITION_PROMOTION_CONFIG"] = str(self.promotion_path)

    def tearDown(self):
        shutil.rmtree(self.temp_root, ignore_errors=True)
        for key in ("AAIS_RUNTIME_DIR", "UGR_COGNITION_PROMOTION_CONFIG"):
            os.environ.pop(key, None)

    def test_compare_deliberation_results_perfect_match(self):
        belief = {
            "subject": "runtime",
            "predicate": "status",
            "object": "ok",
            "status": "accepted",
        }
        prod = {"status": "ok", "convergence": {"final_beliefs": [belief]}}
        shadow = {"status": "ok", "convergence": {"final_beliefs": [belief]}}
        comparison = compare_deliberation_results(prod, shadow)
        self.assertEqual(comparison["belief_match_rate"], 1.0)
        self.assertTrue(comparison["status_match"])

    def test_cicd_promotes_on_perfect_match(self):
        pipeline = CognitionCICDPipeline(promotion_path=self.promotion_path)
        result = pipeline.evaluate_comparison(
            {
                "prod_status": "ok",
                "shadow_status": "ok",
                "belief_match_rate": 1.0,
                "status_match": True,
                "prod_only_signatures": [],
                "shadow_only_signatures": [],
            }
        )
        self.assertEqual(result["promotion"]["decision"], "promote")

    def test_shadow_runtime_evaluator_runs_pair(self):
        prod_root = self.temp_root / "prod-runtime"
        shadow_root = self.temp_root / "prod-runtime-shadow"
        prod = UnifiedGovernedRuntime(runtime_dir=prod_root)
        shadow = UnifiedGovernedRuntime(runtime_dir=shadow_root)
        evaluator = ShadowRuntimeEvaluator(prod_runtime=prod, shadow_runtime=shadow)
        result = evaluator.evaluate({"question": "What is governed runtime convergence?", "intent": "general_qa"})
        self.assertIn("comparison", result)
        self.assertIn("prod", result)
        self.assertIn("shadow", result)


class TestPlatformManifestValidator(unittest.TestCase):
    def test_validator_retired_without_wolf_forge(self):
        script = Path(__file__).resolve().parents[1] / "wolf-cog-os" / "scripts" / "validate-ugr-platform-manifest.py"
        if script.is_file():
            import subprocess
            import sys

            completed = subprocess.run(
                [sys.executable, str(script), "--mode", "fail"],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stdout + completed.stderr)
        else:
            self.skipTest("wolf-cog-os UGR platform manifest validator removed")


if __name__ == "__main__":
    unittest.main()
