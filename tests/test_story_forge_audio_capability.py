from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.capabilities.story_forge_audio import (
    STORY_FORGE_AUDIO_CAPABILITY_COMPONENT_ID,
    ensure_story_forge_audio_capability_registered,
    ensure_story_forge_src,
    run_story_forge_audio_capability,
)
from src.phase_gate import Phase, demote_component, reset_registry


STORY_FORGE_SRC = ensure_story_forge_src()

from story_forge.backend_full_build import StoryForgeBackendPipeline
from story_forge.contracts.cinematic import CinematicPlan
from story_forge.contracts.directional import DirectionalContext
from story_forge.contracts.engine_handoff import EngineHandoffInput
from story_forge.contracts.pipeline import FORMAT_SCREENPLAY, LUMEN_MODE_CINEMATIC
from story_forge.contracts.presentation import PresentedOutput
from story_forge.contracts.staging import StagedPlan, StagedUnit, Transition
from story_forge.contracts.translation import Act, SceneGrammar, SceneUnit
from story_forge.movie_audio_pipeline import ensure_audio_pipeline_src, resolve_audio_pipeline_src


ensure_audio_pipeline_src()


class TestStoryForgeAudioCapability(unittest.TestCase):
    def setUp(self) -> None:
        reset_registry()
        self.test_root = Path(tempfile.mkdtemp(prefix="aais_story_forge_audio_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.test_root, ignore_errors=True)

    def test_story_forge_src_defaults_to_vendored_repo_copy(self) -> None:
        expected = Path(__file__).resolve().parents[1] / "external" / "story_forge" / "src"
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AAIS_STORY_FORGE_SRC", None)
            resolved = ensure_story_forge_src()
        self.assertEqual(resolved, expected.resolve())

    def test_audio_pipeline_src_defaults_to_vendored_repo_copy(self) -> None:
        expected = Path(__file__).resolve().parents[1] / "external" / "beatbox_speakers" / "src"
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("STORY_FORGE_AUDIO_PIPELINE_SRC", None)
            resolved = resolve_audio_pipeline_src()
        self.assertEqual(resolved, expected.resolve())

    def _handoff(self) -> EngineHandoffInput:
        scene_one = SceneUnit(
            scene_id="scene_001",
            title="Opening Threshold",
            summary="A gate opens over black water.",
            emotional_tags=["dread"],
            structural_markers=["opening"],
        )
        scene_two = SceneUnit(
            scene_id="scene_002",
            title="Witness Turn",
            summary="The witness names the cost.",
            emotional_tags=["recognition"],
            structural_markers=["turn"],
        )
        grammar = SceneGrammar(
            title="Pipeline Demo",
            acts=[Act(act_id="act_01", title="Act One", scenes=[scene_one, scene_two])],
            total_scenes=2,
            emotional_tags=["dread", "recognition"],
            structural_markers=["opening", "turn"],
            implemented=True,
            valid=True,
        )
        staged = StagedPlan(
            progression_plan="Source-order scaffold.",
            staged_units=[
                StagedUnit(
                    scene_id="scene_001",
                    title="Opening Threshold",
                    summary="A gate opens over black water.",
                    act_id="act_01",
                    order_index=1,
                ),
                StagedUnit(
                    scene_id="scene_002",
                    title="Witness Turn",
                    summary="The witness names the cost.",
                    act_id="act_01",
                    order_index=2,
                ),
            ],
            transitions=[
                Transition(
                    from_scene_id="scene_001",
                    to_scene_id="scene_002",
                    transition_type="source_order",
                    rationale="preserve extracted order",
                )
            ],
            escalation_points=[2],
            implemented=True,
            valid=True,
        )
        presented = PresentedOutput(
            text="HERO: Hold the gate.\nVILLAIN: Then drown with it.",
            format=FORMAT_SCREENPLAY,
            lumen_mode=LUMEN_MODE_CINEMATIC,
            staged_units=staged.staged_units,
            implemented=True,
            valid=True,
        )
        directional = DirectionalContext(
            target="movie",
            priorities=["continuity", "visual rhythm"],
            constraints=["cinematic target only"],
            valid=True,
        )
        return EngineHandoffInput(
            scene_grammar=grammar,
            staged_plan=staged,
            directional_context=directional,
            presented_output=presented,
            cinematic_plan=CinematicPlan(implemented=True, valid=True),
        )

    def _artifact(self):
        pipeline = StoryForgeBackendPipeline(output_root=self.test_root / "backend")
        return pipeline.run_from_handoff(
            session_id="session_story_audio_capability",
            handoff=self._handoff(),
            source_mode="text",
            source_path="story://demo",
            source_title="Pipeline Demo",
        )

    def _request(self) -> dict[str, object]:
        artifact = self._artifact()
        video_path = self.test_root / "video" / "story_no_audio.mp4"
        video_path.parent.mkdir(parents=True, exist_ok=True)
        video_path.write_bytes(b"fake mp4 bytes")
        return {
            "artifact": artifact,
            "rendered_video_path": str(video_path),
            "output_root": str(self.test_root / "audio"),
            "movie_output_path": str(self.test_root / "audio" / "output" / "final_movie.mp4"),
            "runtime_context": "test_harness",
        }

    def test_capability_determinism(self) -> None:
        request = self._request()

        def fake_assemble(req):
            out = Path(req.output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b"assembled movie")
            return str(out)

        with patch("audio_pipeline.orchestrator._now", return_value="2026-01-01T00:00:00+00:00"), patch(
            "audio_pipeline.full_pipeline_runner._now", return_value="2026-01-01T00:00:00+00:00"
        ), patch("audio_pipeline.full_pipeline_runner.verify_ffmpeg", return_value=(True, "ffmpeg")), patch(
            "audio_pipeline.full_pipeline_runner.assemble_movie", side_effect=fake_assemble
        ):
            out1 = run_story_forge_audio_capability(request)
            out2 = run_story_forge_audio_capability(request)

        self.assertEqual(out1, out2)
        self.assertEqual(out1["status"], "completed")

    def test_authority_blocks_execution(self) -> None:
        request = self._request()
        request["runtime_context"] = "operator_runtime"
        ensure_story_forge_audio_capability_registered()
        demote_component(
            STORY_FORGE_AUDIO_CAPABILITY_COMPONENT_ID,
            Phase.PROTOTYPE,
            reason="Operator capability is not admitted for execution.",
            actor="test_harness",
        )

        with patch("story_forge.movie_audio_pipeline.run_story_forge_movie_audio_pipeline") as run_mock:
            result = run_story_forge_audio_capability(request)

        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["error_type"], "AuthorityRejected")
        run_mock.assert_not_called()

    def test_missing_fields_are_rejected_with_reason(self) -> None:
        artifact = self._artifact()
        request = {
            "artifact": artifact,
            "runtime_context": "test_harness",
        }

        with patch("story_forge.movie_audio_pipeline.run_story_forge_movie_audio_pipeline") as run_mock:
            result = run_story_forge_audio_capability(request)

        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["error_type"], "ValidationRejected")
        self.assertIn("rendered_video_path", result["message"])
        run_mock.assert_not_called()

    def test_completed_output_carries_session_and_scene_ids(self) -> None:
        request = self._request()

        def fake_assemble(req):
            out = Path(req.output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b"assembled movie")
            return str(out)

        with patch("audio_pipeline.full_pipeline_runner.verify_ffmpeg", return_value=(True, "ffmpeg")), patch(
            "audio_pipeline.full_pipeline_runner.assemble_movie", side_effect=fake_assemble
        ):
            result = run_story_forge_audio_capability(request)

        artifact = request["artifact"]
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["session_id"], artifact.session_id)
        self.assertEqual(result["scene_id"], artifact.export_package.scene_id)
        self.assertEqual(result["run_id"], artifact.build_id)
        self.assertTrue(result["final_audio_path"])
        self.assertTrue(result["movie_path"])


if __name__ == "__main__":
    unittest.main()
