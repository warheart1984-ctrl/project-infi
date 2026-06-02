from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.capabilities.narrative_trust_pack import (
    apply_signoff,
    build_pack_from_capability_output,
    load_pack,
    verify_pack_integrity,
)
from src.capabilities.story_forge_audio import (
    ensure_story_forge_audio_capability_registered,
    ensure_story_forge_src,
    run_story_forge_audio_capability,
)
from src.phase_gate import reset_registry

STORY_FORGE_SRC = ensure_story_forge_src()

from story_forge.backend_full_build import StoryForgeBackendPipeline
from story_forge.contracts.cinematic import CinematicPlan
from story_forge.contracts.directional import DirectionalContext
from story_forge.contracts.engine_handoff import EngineHandoffInput
from story_forge.contracts.pipeline import FORMAT_SCREENPLAY, LUMEN_MODE_CINEMATIC
from story_forge.contracts.presentation import PresentedOutput
from story_forge.contracts.staging import StagedPlan, StagedUnit, Transition
from story_forge.contracts.translation import Act, SceneGrammar, SceneUnit
from story_forge.movie_audio_pipeline import ensure_audio_pipeline_src

ensure_audio_pipeline_src()


class TestNarrativeTrustPack(unittest.TestCase):
    def setUp(self) -> None:
        reset_registry()
        ensure_story_forge_audio_capability_registered()
        self.test_root = Path(tempfile.mkdtemp(prefix="ntp_test_"))
        self.narrative_root = self.test_root / "narrative"

    def tearDown(self) -> None:
        shutil.rmtree(self.test_root, ignore_errors=True)

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
            session_id="session_ntp_demo",
            handoff=self._handoff(),
            source_mode="text",
            source_path="story://demo",
            source_title="Pipeline Demo",
        )

    def _run_capability(self) -> dict:
        artifact = self._artifact()
        video_path = self.test_root / "video" / "render.mp4"
        video_path.parent.mkdir(parents=True, exist_ok=True)
        video_path.write_bytes(b"fake mp4 bytes")

        request = {
            "artifact": artifact,
            "rendered_video_path": str(video_path),
            "output_root": str(self.test_root / "audio"),
            "movie_output_path": str(self.test_root / "audio" / "output" / "final_movie.mp4"),
            "runtime_context": "test_harness",
        }

        def fake_assemble(req):
            out = Path(req.output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b"assembled movie")
            return str(out)

        with patch("audio_pipeline.full_pipeline_runner.verify_ffmpeg", return_value=(True, "ffmpeg")), patch(
            "audio_pipeline.full_pipeline_runner.assemble_movie", side_effect=fake_assemble
        ):
            return run_story_forge_audio_capability(request)

    def test_e2e_pack_signoff_proven(self) -> None:
        output = self._run_capability()
        self.assertEqual(output["status"], "completed")
        artifact = self._artifact()
        metadata_path = Path(artifact.metadata_path)
        pack = build_pack_from_capability_output(
            output,
            pack_id="ntp-demo-001",
            author="test_harness",
            story_forge_artifact_path=metadata_path,
            root=self.narrative_root,
        )
        self.assertEqual(pack["claim_label"], "asserted")
        self.assertFalse(pack["export_ready"])
        self.assertGreaterEqual(len(pack["stages"]), 2)

        signed = apply_signoff(pack, signoff_by="human@local")
        self.assertEqual(signed["claim_label"], "proven")
        self.assertTrue(signed["export_ready"])

        loaded = load_pack("ntp-demo-001", root=self.narrative_root)
        self.assertEqual(loaded["pack_id"], "ntp-demo-001")

    def test_tamper_rejects_signoff(self) -> None:
        output = self._run_capability()
        artifact = self._artifact()
        pack = build_pack_from_capability_output(
            output,
            pack_id="ntp-tamper-001",
            author="test_harness",
            story_forge_artifact_path=Path(artifact.metadata_path),
            root=self.narrative_root,
        )
        tamper_path = Path(pack["stages"][0]["artifact_path"])
        tamper_path.write_bytes(tamper_path.read_bytes() + b"tampered")
        verify = verify_pack_integrity(pack)
        self.assertFalse(verify["ok"])
        self.assertEqual(verify["claim_label"], "rejected")
        signed = apply_signoff(pack, signoff_by="human@local")
        self.assertEqual(signed["claim_label"], "rejected")
        self.assertFalse(signed.get("export_ready"))


if __name__ == "__main__":
    unittest.main()
