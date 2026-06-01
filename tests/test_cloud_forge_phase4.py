from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.cloud_forge.integration import schedule_request_observed
from src.cloud_forge.locality import (
    SessionPrewarmStore,
    build_cloud_placement,
    map_governance_to_priority,
    resolve_domain_slice,
)
from src.cloud_forge.tempering import run_tempering_dry_run, write_tempering_report
from src.cloud_forge.templates import DOMAIN_FORGE_VOSS_OS
from src.cloud_forge.types import ClusterState, GovernanceWeight, LawEnvelope, PerformanceProfile


class CloudForgeLocalityTests(unittest.TestCase):
    def test_resolve_forge_voss_slice(self) -> None:
        sl = resolve_domain_slice(DOMAIN_FORGE_VOSS_OS)
        self.assertEqual(sl["slice_id"], "forge-voss-os")
        self.assertEqual(sl["namespace"], "cloud-forge-forge-voss")

    def test_priority_mapping_high_weight(self) -> None:
        actor = GovernanceWeight.from_dict({"wL": 200, "wT": 150, "wI": 180})
        tenant = PerformanceProfile.from_dict({"latency_bias": 0.5, "throughput_bias": 0.3, "intelligence_bias": 0.2})
        priority = map_governance_to_priority(actor, tenant, ClusterState(load="low"))
        self.assertIn(priority["priority_class"], ("cloud-forge-critical", "cloud-forge-high"))

    def test_session_prewarm_cache_hit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = SessionPrewarmStore(Path(tmp) / "prewarm")
            law = LawEnvelope(law_id="meta.architect.v1", law_version="2026-05-28")
            tenant = PerformanceProfile()
            actor = GovernanceWeight.from_dict({"wL": 120})
            first = store.resolve_or_create("t1", "sess-1", law, tenant, actor, DOMAIN_FORGE_VOSS_OS)
            self.assertFalse(first["cache_hit"])
            second = store.resolve_or_create("t1", "sess-1", law, tenant, actor, DOMAIN_FORGE_VOSS_OS)
            self.assertTrue(second["cache_hit"])

    def test_build_cloud_placement(self) -> None:
        placement = build_cloud_placement(
            actor=GovernanceWeight.from_dict({"wL": 120}),
            tenant=PerformanceProfile(),
            domain=DOMAIN_FORGE_VOSS_OS,
        )
        self.assertTrue(placement["forge_voss_os_slice"])
        self.assertIn("llm-gateway", placement["components"])


class CloudForgeTemperingTests(unittest.TestCase):
    def test_tempering_dry_run_from_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "rail.jsonl"
            row = {
                "rail_decision": {"rail": "EXPRESS", "risk": "LOW"},
                "cognition_plan": {"domain_template": DOMAIN_FORGE_VOSS_OS},
                "task_snapshot": {"domain": DOMAIN_FORGE_VOSS_OS},
            }
            ledger_path.write_text(
                json.dumps(row) + "\n" + json.dumps(row) + "\n",
                encoding="utf-8",
            )
            report = run_tempering_dry_run(ledger_path=ledger_path)
            self.assertFalse(report.get("skipped"))
            self.assertEqual(report["record_count"], 2)
            self.assertIn(DOMAIN_FORGE_VOSS_OS, report["express_candidates"])

    def test_tempering_skip_env(self) -> None:
        with mock.patch.dict(os.environ, {"CLOUD_FORGE_TEMPERING_SKIP": "1"}):
            report = run_tempering_dry_run(ledger_path=Path("/nonexistent"))
        self.assertTrue(report.get("skipped"))

    def test_write_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            write_tempering_report({"ok": True, "claim_status": "asserted"}, out)
            self.assertTrue(out.is_file())


class CloudForgePhase4IntegrationTests(unittest.TestCase):
    def test_observed_includes_cloud_placement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "CLOUD_FORGE_CACHE_ROOT": str(Path(tmp) / "cache"),
                "CLOUD_FORGE_LEDGER_PATH": str(Path(tmp) / "rail.jsonl"),
                "CLOUD_FORGE_PREWARM_ROOT": str(Path(tmp) / "prewarm"),
            }
            with mock.patch.dict(os.environ, env, clear=False):
                bundle = schedule_request_observed(
                    task={
                        "task_id": "t-p4",
                        "pattern_class": "docs_explanation",
                        "mutation_scope": "none",
                        "domain": DOMAIN_FORGE_VOSS_OS,
                    },
                    actor={"wL": 200, "wT": 150, "wI": 150},
                    tenant={"latency_bias": 0.4},
                    law_envelope={
                        "law_id": "meta.architect.v1",
                        "law_version": "2026-05-28",
                        "signals": ["read_only", "docs", "governance"],
                    },
                    tenant_id="tenant-p4",
                    session_id="session-p4-1",
                    log_ledger=False,
                )
            self.assertIn("cloud_placement", bundle)
            self.assertEqual(bundle["cloud_placement"]["slice_id"], "forge-voss-os")
            self.assertIn("session_prewarm", bundle)
            self.assertGreaterEqual(bundle["cognition_plan"]["parallelism"], 2)


if __name__ == "__main__":
    unittest.main()
