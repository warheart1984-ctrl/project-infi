from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from src.cloud_forge.failsafe import FORCE_SAFE_ENV
from src.governed_direct_pipeline import build_governed_turn_pipeline
from src.cloud_forge.rails import (
    attach_cloud_forge_to_pipeline,
    build_plan,
    choose_rail,
    schedule_request,
)
from src.cloud_forge.risk import estimate_novelty, estimate_risk
from src.cloud_forge.types import (
    GovernanceWeight,
    LawEnvelope,
    PerformanceProfile,
    Rail,
    RiskLevel,
    TaskSignature,
)


def _task(**overrides) -> TaskSignature:
    base = {
        "task_id": "t-1",
        "pattern_class": "docs_explanation",
        "mutation_scope": "none",
        "domain": "forge/voss/os_architecture",
    }
    base.update(overrides)
    return TaskSignature.from_dict(base)


def _law(**overrides) -> LawEnvelope:
    base = {
        "law_id": "meta.architect.v1",
        "law_version": "2026-05-28",
        "signals": ["read_only", "docs"],
    }
    base.update(overrides)
    return LawEnvelope.from_dict(base)


def _tenant(**overrides) -> PerformanceProfile:
    return PerformanceProfile.from_dict(overrides or {})


def _actor(**overrides) -> GovernanceWeight:
    base = {"wL": 120, "wT": 80, "wI": 200}
    base.update(overrides)
    return GovernanceWeight.from_dict(base)


class CloudForgeRiskTests(unittest.TestCase):
    def test_constitutional_scope_is_high(self) -> None:
        risk = estimate_risk(
            _task(mutation_scope="constitutional"),
            _law(),
        )
        self.assertEqual(risk, RiskLevel.HIGH)

    def test_required_proof_is_high(self) -> None:
        risk = estimate_risk(_task(), _law(required_proof=True))
        self.assertEqual(risk, RiskLevel.HIGH)

    def test_docs_none_scope_is_low(self) -> None:
        risk = estimate_risk(_task(), _law())
        self.assertEqual(risk, RiskLevel.LOW)

    def test_write_non_prod_is_medium(self) -> None:
        risk = estimate_risk(
            _task(mutation_scope="write", pattern_class="refactor_module"),
            _law(),
        )
        self.assertEqual(risk, RiskLevel.MEDIUM)

    def test_novelty_phase1_is_medium(self) -> None:
        self.assertEqual(estimate_novelty(_task()), RiskLevel.MEDIUM)


class CloudForgeRailTests(unittest.TestCase):
    def test_constitutional_forces_safe(self) -> None:
        decision = choose_rail(
            _task(mutation_scope="constitutional"),
            _actor(),
            _tenant(),
            law_envelope=_law(),
        )
        self.assertEqual(decision.rail, Rail.SAFE)
        self.assertIn("risk.high", decision.rationale_codes)

    def test_required_proof_forces_safe(self) -> None:
        decision = choose_rail(
            _task(),
            _actor(),
            _tenant(),
            law_envelope=_law(required_proof=True),
        )
        self.assertEqual(decision.rail, Rail.SAFE)
        self.assertIn("law.required_proof", decision.rationale_codes)

    def test_low_risk_defaults_to_express(self) -> None:
        decision = choose_rail(
            _task(),
            _actor(wL=120),
            _tenant(latency_bias=0.4, wL_express_threshold=100, wL_express_floor=50),
            law_envelope=_law(),
        )
        self.assertEqual(decision.rail, Rail.EXPRESS)
        self.assertIn("risk.low", decision.rationale_codes)

    def test_weight_grant_after_floor_cap(self) -> None:
        decision = choose_rail(
            _task(),
            _actor(wL=90),
            _tenant(wL_express_floor=100, wL_express_threshold=80, latency_bias=0.4),
            law_envelope=_law(),
        )
        self.assertEqual(decision.rail, Rail.EXPRESS)
        self.assertIn("weight.express_denied", decision.rationale_codes)
        self.assertIn("weight.express_granted", decision.rationale_codes)

    def test_low_risk_low_weight_denies_express(self) -> None:
        decision = choose_rail(
            _task(),
            _actor(wL=30),
            _tenant(wL_express_floor=50),
            law_envelope=_law(),
        )
        self.assertEqual(decision.rail, Rail.NORMAL)
        self.assertIn("weight.express_denied", decision.rationale_codes)

    def test_medium_write_never_express(self) -> None:
        decision = choose_rail(
            _task(mutation_scope="write", pattern_class="refactor_module"),
            _actor(wL=200),
            _tenant(latency_bias=0.9),
            law_envelope=_law(),
        )
        self.assertEqual(decision.rail, Rail.NORMAL)
        self.assertEqual(decision.law_ceiling, Rail.NORMAL)

    def test_forbid_express_caps_at_normal(self) -> None:
        decision = choose_rail(
            _task(),
            _actor(wL=200),
            _tenant(latency_bias=0.9),
            law_envelope=_law(forbid_express=True),
        )
        self.assertEqual(decision.rail, Rail.NORMAL)
        self.assertIn("law.forbid_express", decision.rationale_codes)

    def test_force_safe_env(self) -> None:
        with mock.patch.dict(os.environ, {FORCE_SAFE_ENV: "1"}):
            decision = choose_rail(
                _task(),
                _actor(wL=200),
                _tenant(),
                law_envelope=_law(),
            )
        self.assertEqual(decision.rail, Rail.SAFE)
        self.assertIn("failsafe.force_safe", decision.rationale_codes)

    def test_immune_elevated_forces_safe(self) -> None:
        decision = choose_rail(
            _task(),
            _actor(wL=200),
            _tenant(),
            law_envelope=_law(),
            immune_elevated=True,
        )
        self.assertEqual(decision.rail, Rail.SAFE)
        self.assertIn("immune.elevated", decision.rationale_codes)


class CloudForgePlanTests(unittest.TestCase):
    def test_safe_plan_minimal_cache_and_speculation(self) -> None:
        decision = choose_rail(
            _task(mutation_scope="constitutional"),
            _actor(),
            _tenant(),
            law_envelope=_law(),
        )
        plan = build_plan(_task(mutation_scope="constitutional"), decision, _actor(), _tenant(), law_envelope=_law())
        self.assertEqual(plan.steps, ["ANALYZE", "PLAN", "TOOLS", "DRAFT", "CRITIQUE", "FINAL"])
        self.assertEqual(plan.cache_mode, "off")
        self.assertEqual(plan.speculation, "off")
        self.assertEqual(plan.parallelism, 1)

    def test_express_plan_compressed_chain(self) -> None:
        decision = choose_rail(_task(), _actor(wL=120), _tenant(), law_envelope=_law())
        plan = build_plan(_task(), decision, _actor(wL=120), _tenant(), law_envelope=_law())
        self.assertEqual(plan.steps, ["PLAN_TOOLS", "FINAL"])
        self.assertEqual(plan.domain_template, "forge/voss/os_architecture")

    def test_cache_capped_by_law(self) -> None:
        decision = choose_rail(_task(), _actor(wL=120), _tenant(), law_envelope=_law())
        plan = build_plan(
            _task(),
            decision,
            _actor(wL=120),
            _tenant(),
            law_envelope=_law(forbid_cache_above="L0"),
        )
        self.assertEqual(plan.cache_mode, "L0")


class CloudForgeIntegrationTests(unittest.TestCase):
    def test_schedule_request_bundle(self) -> None:
        bundle = schedule_request(
            task=_task(),
            actor=_actor(),
            tenant=_tenant(),
            law_envelope=_law(),
        )
        self.assertEqual(bundle["contract_version"], "aais.cloud_forge.rail.v1")
        self.assertIn("rail_decision", bundle)
        self.assertIn("cognition_plan", bundle)
        self.assertEqual(bundle["rail_decision"]["rail"], "EXPRESS")

    def test_attach_to_pipeline(self) -> None:
        pipeline = {"pipeline_id": "gdp_test", "summary": "test"}
        updated = attach_cloud_forge_to_pipeline(
            pipeline,
            {
                "task": {
                    "task_id": "t-1",
                    "pattern_class": "docs_explanation",
                    "mutation_scope": "none",
                },
                "actor": {"wL": 30},
                "tenant": {},
                "law_envelope": {
                    "law_id": "meta.architect.v1",
                    "law_version": "2026-05-28",
                    "signals": ["read_only", "docs"],
                },
                "log_ledger": False,
                "apply_domain_template": False,
            },
        )
        self.assertIn("cloud_forge", updated)
        self.assertEqual(updated["cloud_forge"]["rail_decision"]["rail"], "NORMAL")

    @mock.patch(
        "src.cognitive_bridge.route_to_bridge",
        return_value={"decision": "ALLOW"},
    )
    def test_pipeline_cloud_forge_hook(self, _mock_bridge) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = os.path.join(tmp, "rail.jsonl")
            with mock.patch.dict(os.environ, {"CLOUD_FORGE_LEDGER_PATH": ledger_path}):
                pipeline = build_governed_turn_pipeline(
                    response_mode="fast",
                    contract="direct_answer",
                    cloud_forge_context={
                        "task": {
                            "task_id": "gdp-1",
                            "pattern_class": "docs_explanation",
                            "mutation_scope": "none",
                        },
                        "actor": {"wL": 120},
                        "tenant": {"latency_bias": 0.4},
                        "law_envelope": {
                            "law_id": "meta.architect.v1",
                            "law_version": "2026-05-28",
                            "signals": ["read_only", "docs"],
                        },
                        "log_ledger": False,
                        "apply_domain_template": False,
                    },
                )
        self.assertIn("cloud_forge", pipeline)
        self.assertEqual(
            pipeline["cloud_forge"]["cognition_plan"]["steps"],
            ["PLAN_TOOLS", "FINAL"],
        )


if __name__ == "__main__":
    unittest.main()
