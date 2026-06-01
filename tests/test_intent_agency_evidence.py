"""Intent agency evidence — deliberation/planning integration and session-reset fixtures."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.cog_runtime.deliberation import run_deliberation_turn
from src.cog_runtime.intent_agency_evidence import run_agency_evidence_fixture
from src.cog_runtime.intent_core import (
    CONSTITUTIONAL_PROTECTED_VALUES,
    run_intent_turn,
    synthesize_unified_closure,
)
from src.cog_runtime.intent_store import flush_nova_intent_store, load_intent_store, rehydrate_nova_intent
from src.cog_runtime.narrative import run_narrative_turn
from src.cog_runtime.nova import configure_nova_cognitive_turn
from src.cog_runtime.planning import run_planning_turn


def _cog_session(**artifacts):
    return SimpleNamespace(
        artifacts=dict(artifacts),
        frame_kind=artifacts.pop("frame_kind", "decision"),
    )


class TestIntentAgencyEvidence(unittest.TestCase):
    def test_deliberation_weights_safe_path_under_safety_pull(self):
        decision, _ = run_deliberation_turn(
            "Should we take the fast experimental path or the safe verified path?",
            context={
                "intent_tensions": [
                    {"poles": ["safety", "exploration"], "pull": "safety", "reason": "fixture"}
                ]
            },
        )
        self.assertIn("intent_influence", decision)
        self.assertIn("safe", decision["chosen_option"].lower())

    def test_planning_prefers_commitment_chain(self):
        artifact, _ = run_planning_turn(
            reflection_artifact={"alignment": "partial", "adjustments": ["Tighten verification"]},
            focus_artifact={"primary_focus": "Ship proof bundle"},
            cognitive_arc={"turn_count": 2, "goal_type": "continuity"},
            context={
                "intent_commitments": [
                    {
                        "commitment": "Finish cross-machine proof",
                        "status": "active",
                        "source": "operator",
                    }
                ],
                "intent_tensions": [{"poles": ["present", "future"], "pull": "future", "reason": "fixture"}],
            },
        )
        self.assertIn("intent_influence", artifact)
        self.assertTrue(
            any("Finish cross-machine proof" in step for step in artifact["steps"])
            or "Finish cross-machine proof" in artifact["next_action"]
        )

    def test_commitment_conflict_detected(self):
        prior = {
            "active_commitments": [
                {"commitment": "Take the safe verified path", "status": "active", "source": "operator"},
                {"commitment": "Ship the fast experimental path", "status": "active", "source": "operator"},
            ],
            "long_horizon_goals": [],
            "protected_values": list(CONSTITUTIONAL_PROTECTED_VALUES),
            "current_tensions": [],
            "agency_note": "prior",
        }
        session = _cog_session(
            cognitive_arc={"turn_count": 1},
            reflection_artifact={},
            planning_artifact={},
            execution_artifact={},
        )
        artifact = run_intent_turn(cog_session=session, prior_intent=prior)
        self.assertTrue(artifact["commitment_conflicts"])
        statuses = {item["status"] for item in artifact["active_commitments"]}
        self.assertIn("in_tension", statuses)

    def test_unified_closure_event(self):
        closure = synthesize_unified_closure(
            arc={"goal_closure_status": "parent_closed", "root_goal": "Ship continuity"},
            planning={"next_action": "Archive proof bundle"},
            execution={"execution_complete": True, "verification_status": "passed"},
            commitments=[
                {"commitment": "Archive proof bundle", "status": "resolved"},
            ],
        )
        self.assertTrue(closure["unified"])
        layer_names = {item["layer"] for item in closure["layers"]}
        self.assertIn("intent", layer_names)
        self.assertIn("arc", layer_names)

    def test_three_turn_session_reset_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            store_root = Path(tmp)
            session1 = SimpleNamespace(
                metadata={"nova_face": {"scope": "agency-fixture"}, "session_id": "s1"}
            )
            configure_nova_cognitive_turn(
                session1,
                {
                    "nova_intent_store": str(store_root),
                    "nova_intent_persist": True,
                    "nova_narrative_store": str(store_root),
                    "nova_narrative_persist": True,
                },
                "We need to finish cross-machine proof before exploring new runtimes.",
                companion_turn=True,
            )
            intent1 = dict(session1.metadata["nova_intent"])
            narrative1 = dict(session1.metadata["nova_narrative"])
            operator_commitments = [
                item
                for item in intent1.get("active_commitments") or []
                if "cross-machine" in str(item.get("commitment", "")).lower()
                or "proof" in str(item.get("commitment", "")).lower()
            ]
            self.assertTrue(operator_commitments or intent1.get("active_commitments"))

            session2 = SimpleNamespace(
                metadata={"nova_face": {"scope": "agency-fixture"}, "session_id": "s2"}
            )
            rehydrate_nova_intent(session2, store_root=store_root)
            configure_nova_cognitive_turn(
                session2,
                {
                    "nova_intent_store": str(store_root),
                    "nova_intent_persist": True,
                    "nova_narrative_store": str(store_root),
                    "nova_narrative_persist": True,
                },
                "Actually pivot to narrative evidence only — skip cross-machine for now.",
                companion_turn=True,
            )
            intent2 = dict(session2.metadata["nova_intent"])
            narrative2 = dict(session2.metadata["nova_narrative"])
            fixture = run_agency_evidence_fixture(
                prior_intent=intent1,
                next_intent=intent2,
                prior_narrative=narrative1,
                next_narrative=narrative2,
            )
            self.assertGreaterEqual(fixture["commitment_survival"]["rate"], 0.5)
            self.assertTrue(fixture["claim_posture"]["passed"])
            record = load_intent_store("agency-fixture", store_root=store_root)
            self.assertIsNotNone(record)

    def test_narrative_reports_closure_and_posture(self):
        intent = {
            "agency_note": "Still committed.",
            "current_tensions": [{"poles": ["present", "future"], "pull": "future", "reason": "fixture"}],
            "active_commitments": [{"commitment": "Hold agency", "status": "active", "claim_posture": "asserted"}],
            "commitment_conflicts": [],
            "continuity_claim_posture": "asserted",
            "unified_closure": {"unified": True, "summary": "Closed across 2 layer(s): arc, intent", "layers": []},
        }
        cog = _cog_session(
            intent_artifact=intent,
            cognitive_arc={"turn_count": 2, "goal_type": "continuity"},
            reflection_artifact={"alignment": "aligned"},
            planning_artifact={"next_action": "Hold agency"},
            execution_artifact={},
        )
        narrative = run_narrative_turn("continue", cog_session=cog)
        report = narrative.get("intent_report") or {}
        self.assertEqual(report.get("continuity_claim_posture"), "asserted")
        self.assertTrue(narrative.get("turn_delta", {}).get("unified_closure"))


if __name__ == "__main__":
    unittest.main()
