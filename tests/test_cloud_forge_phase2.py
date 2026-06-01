from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.cloud_forge.integration import enrich_preview_with_cloud_forge, schedule_request_observed
from src.cloud_forge.ledger import RailDecisionLedger
from src.cloud_forge.promotion import submit_rail_promotion_candidate
from src.cloud_forge.risk import estimate_novelty
from src.cloud_forge.templates import DOMAIN_FORGE_VOSS_OS, apply_task_template_defaults, enrich_plan_with_template
from src.cloud_forge.types import Rail, RiskLevel, TaskSignature


def _forge_task(**overrides) -> TaskSignature:
    base = {
        "task_id": "t-forge-1",
        "pattern_class": "unknown",
        "mutation_scope": "none",
        "domain": DOMAIN_FORGE_VOSS_OS,
        "normalized_prompt_hash": "sha256:forge-arch-abc",
    }
    base.update(overrides)
    return TaskSignature.from_dict(base)


class CloudForgeTemplateTests(unittest.TestCase):
    def test_apply_domain_defaults(self) -> None:
        task = apply_task_template_defaults(_forge_task(pattern_class="unknown"))
        self.assertEqual(task.pattern_class, "docs_explanation")
        self.assertIn("doc_search", task.tool_intents)

    def test_enrich_express_plan(self) -> None:
        plan = enrich_plan_with_template(
            {"steps": ["PLAN_TOOLS", "FINAL"], "model_tier": "mid"},
            DOMAIN_FORGE_VOSS_OS,
            Rail.EXPRESS,
        )
        self.assertEqual(plan["domain_template"], DOMAIN_FORGE_VOSS_OS)
        self.assertIn("META_ARCHITECT_LAWBOOK.md", plan["template"]["prefetch_docs"])


class CloudForgeLedgerTests(unittest.TestCase):
    def test_append_and_read_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rail-decisions.jsonl"
            ledger = RailDecisionLedger(path)
            bundle = {
                "contract_version": "aais.cloud_forge.rail.v1",
                "rail_decision": {"task_id": "t-1", "rail": "EXPRESS", "risk": "LOW"},
                "cognition_plan": {"steps": ["PLAN_TOOLS", "FINAL"], "domain_template": DOMAIN_FORGE_VOSS_OS},
                "task_snapshot": {"normalized_prompt_hash": "sha256:x", "domain": DOMAIN_FORGE_VOSS_OS},
            }
            record = ledger.append(bundle, outcome_summary="ok")
            rows = ledger.read_records()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["record_id"], record["record_id"])

    def test_novelty_low_after_repeat(self) -> None:
        records = [
            {
                "task_snapshot": {"normalized_prompt_hash": "sha256:repeat", "domain": DOMAIN_FORGE_VOSS_OS},
                "cognition_plan": {"domain_template": DOMAIN_FORGE_VOSS_OS},
                "rail_decision": {"rail": "EXPRESS"},
            },
            {
                "task_snapshot": {"normalized_prompt_hash": "sha256:repeat", "domain": DOMAIN_FORGE_VOSS_OS},
                "cognition_plan": {"domain_template": DOMAIN_FORGE_VOSS_OS},
                "rail_decision": {"rail": "NORMAL"},
            },
        ]
        task = TaskSignature.from_dict(
            {
                "task_id": "t",
                "pattern_class": "docs_explanation",
                "mutation_scope": "none",
                "domain": DOMAIN_FORGE_VOSS_OS,
                "normalized_prompt_hash": "sha256:repeat",
            }
        )
        self.assertEqual(estimate_novelty(task, records), RiskLevel.LOW)


class CloudForgePromotionTests(unittest.TestCase):
    def test_promotion_stub_pending_review(self) -> None:
        promo = submit_rail_promotion_candidate(
            {
                "record_id": "rail-abc",
                "rail_decision": {"rail": "EXPRESS", "risk": "LOW"},
                "cognition_plan": {"domain_template": DOMAIN_FORGE_VOSS_OS},
            },
            classification="success",
        )
        self.assertEqual(promo["classification"], "pending_review")
        self.assertFalse(promo["auto_publish"])
        self.assertFalse(promo["hall_of_fame_eligible"])


class CloudForgeObservedTests(unittest.TestCase):
    def test_schedule_observed_forge_domain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rail.jsonl"
            with mock.patch.dict(os.environ, {"CLOUD_FORGE_LEDGER_PATH": str(path)}):
                bundle = schedule_request_observed(
                    task=_forge_task(),
                    actor={"wL": 120},
                    tenant={"latency_bias": 0.4},
                    law_envelope={
                        "law_id": "meta.architect.v1",
                        "law_version": "2026-05-28",
                        "signals": ["read_only", "docs", "governance"],
                    },
                )
            self.assertEqual(bundle["cognition_plan"]["domain_template"], DOMAIN_FORGE_VOSS_OS)
            self.assertIn("ledger_record_id", bundle)
            self.assertIn("cloud_forge_readout", bundle)
            self.assertEqual(bundle["promotion_candidate"]["classification"], "pending_review")
            self.assertTrue(path.exists())
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            row = json.loads(lines[0])
            self.assertEqual(row["source_class"], "routing_subsystem")

    def test_jarvis_preview_readout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rail.jsonl"
            with mock.patch.dict(os.environ, {"CLOUD_FORGE_LEDGER_PATH": str(path)}):
                preview = enrich_preview_with_cloud_forge(
                    {"guardrail_state": {"status": "nominal"}},
                    {
                        "task": {
                            "task_id": "t-forge-1",
                            "pattern_class": "docs_explanation",
                            "mutation_scope": "none",
                            "domain": DOMAIN_FORGE_VOSS_OS,
                            "normalized_prompt_hash": "sha256:forge-arch-abc",
                        },
                        "actor": {"wL": 120},
                        "tenant": {"latency_bias": 0.4},
                        "law_envelope": {
                            "law_id": "meta.architect.v1",
                            "law_version": "2026-05-28",
                            "signals": ["read_only", "docs", "governance"],
                        },
                    },
                )
            self.assertIn("cloud_forge_readout", preview)
            self.assertEqual(preview["cloud_forge_readout"]["rail"], "EXPRESS")
            self.assertIn("forge/voss/os_architecture", preview["cloud_forge_readout"]["summary"])


if __name__ == "__main__":
    unittest.main()
