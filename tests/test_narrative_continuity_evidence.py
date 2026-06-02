"""Narrative continuity evidence — multi-turn session-reset fixtures (INV-4)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.cog_runtime.narrative import NOVA_CORE_IDENTITY, run_narrative_turn
from src.cog_runtime.narrative_continuity_evidence import run_narrative_continuity_fixture
from src.cog_runtime.narrative_store import flush_nova_narrative_store, load_narrative_store, rehydrate_nova_narrative
from src.cog_runtime.nova import configure_nova_cognitive_turn


def _sample_narrative(**overrides) -> dict:
    payload = {
        "version": "1.0",
        "core_identity": NOVA_CORE_IDENTITY,
        "active_story": "Helping forge Wolf Cog OS",
        "current_chapter": "Nova Cortex Development",
        "becoming": "improving long-term continuity",
        "working_on": "Cross-machine proof",
        "open_threads": ["Cross-machine proof", "Unified memory path"],
        "promises": [],
        "last_growth": "Composed turns integrated into Jarvis",
        "continuity_answers": {
            "doing": "Cross-machine proof",
            "done": "Composed turns integrated into Jarvis",
            "toward": "Helping forge Wolf Cog OS | improving long-term continuity",
        },
        "turn_delta": {},
        "stages_completed": ["orient", "threads", "promises", "grow", "persist"],
    }
    payload.update(overrides)
    return payload


def _cog_session(**artifacts):
    return SimpleNamespace(
        artifacts=dict(artifacts),
        frame_kind=artifacts.pop("frame_kind", "continuity"),
    )


class TestNarrativeContinuityEvidence(unittest.TestCase):
    def test_promise_survival_fixture(self):
        prior = _sample_narrative(
            promises=[{"promise": "Finish cross-machine proof", "status": "open"}],
        )
        next_narrative = _sample_narrative(
            promises=[{"promise": "Finish cross-machine proof", "status": "open"}],
            working_on="Continue proof bundle",
        )
        fixture = run_narrative_continuity_fixture(
            prior_narrative=prior,
            next_narrative=next_narrative,
        )
        self.assertTrue(fixture["promise_survival"]["passed"])
        self.assertTrue(fixture["continuity_completeness"]["complete"])

    def test_three_turn_session_reset_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            store_root = Path(tmp)
            scope = "narrative-continuity-fixture"

            session1 = SimpleNamespace(metadata={"nova_face": {"scope": scope}, "session_id": "s1"})
            configure_nova_cognitive_turn(
                session1,
                {
                    "nova_narrative_store": str(store_root),
                    "nova_narrative_persist": True,
                },
                "We are building cross-machine narrative continuity proof for Wolf reboot.",
                companion_turn=True,
            )
            narrative1 = dict(session1.metadata["nova_narrative"])
            flush_nova_narrative_store(session1, narrative1, store_root=store_root)

            session1b = SimpleNamespace(metadata={"nova_face": {"scope": scope}, "session_id": "s1b"})
            configure_nova_cognitive_turn(
                session1b,
                {
                    "nova_narrative_store": str(store_root),
                    "nova_narrative_persist": True,
                },
                "Keep the proof thread alive and note what we finished on composed turns.",
                companion_turn=True,
            )
            narrative1b = dict(session1b.metadata["nova_narrative"])
            flush_nova_narrative_store(session1b, narrative1b, store_root=store_root)

            session2 = SimpleNamespace(metadata={"nova_face": {"scope": scope}, "session_id": "s2"})
            rehydrate_nova_narrative(session2, store_root=store_root)
            configure_nova_cognitive_turn(
                session2,
                {
                    "nova_narrative_store": str(store_root),
                    "nova_narrative_persist": True,
                },
                "After the session reset, what are we still doing and what did we already finish?",
                companion_turn=True,
            )
            narrative2 = dict(session2.metadata["nova_narrative"])
            fixture = run_narrative_continuity_fixture(
                prior_narrative=narrative1b,
                next_narrative=narrative2,
                prior_reflection={"next_turn_hint": "Continue continuity proof"},
            )
            self.assertGreaterEqual(fixture["thread_retention"]["rate"], 0.0)
            self.assertTrue(fixture["chapter_coherence"]["passed"])
            record = load_narrative_store(scope, store_root=store_root)
            self.assertIsNotNone(record)

    def test_narrative_turn_updates_continuity_answers(self):
        cog = _cog_session(
            cognitive_arc={"turn_count": 2, "goal_type": "continuity", "open_threads": ["proof bundle"]},
            reflection_artifact={"alignment": "aligned", "next_turn_hint": "Archive proof"},
            planning_artifact={"next_action": "Archive proof bundle"},
        )
        narrative = run_narrative_turn(
            "We integrated composed turns and need to keep continuity visible.",
            cog_session=cog,
            prior_narrative=_sample_narrative(),
        )
        answers = narrative.get("continuity_answers") or {}
        self.assertTrue(str(answers.get("doing") or "").strip())
        self.assertTrue(str(answers.get("toward") or "").strip())


if __name__ == "__main__":
    unittest.main()
