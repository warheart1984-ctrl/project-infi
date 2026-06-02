from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from src.capabilities.imagine_generator import run_imagine_generator_capability
from src.imagine_generator import (
    admit_to_story_forge,
    build_pattern,
    build_pattern_from_fixture,
    check_constraints,
    persist_pattern,
    story_forge_admission_path,
)
from src.phase_gate import reset_registry


class TestImagineGenerator(unittest.TestCase):
    def setUp(self) -> None:
        reset_registry()
        self.temp_root = Path(tempfile.mkdtemp(prefix="imagine_test_"))
        self.imagine_root = self.temp_root / "imagine"
        self.story_forge_root = self.temp_root / "story_forge"

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_fixture_emits_valid_pattern(self) -> None:
        pattern = build_pattern_from_fixture("scene-seed-demo")
        self.assertEqual(pattern["imagine_generator_version"], "imagine_generator.v1")
        self.assertEqual(pattern["claim_label"], "asserted")

    def test_forbidden_term_rejects(self) -> None:
        pattern = build_pattern(
            pattern_type="scene_seed",
            prompt_frame="A loud explosion rocks the platform.",
            constraints=[
                {
                    "constraint_id": "f1",
                    "constraint_kind": "forbidden_term",
                    "value": "explosion",
                }
            ],
        )
        self.assertEqual(pattern["claim_label"], "rejected")
        check = check_constraints(pattern)
        self.assertFalse(check["passed"])

    def test_handoff_writes_admission_file(self) -> None:
        pattern = build_pattern_from_fixture("scene-seed-demo")
        persist_pattern(pattern, root=self.imagine_root)
        result = admit_to_story_forge(pattern, story_forge_root=self.story_forge_root)
        self.assertEqual(result["status"], "admitted")
        path = story_forge_admission_path(pattern["pattern_id"], story_forge_root=self.story_forge_root)
        self.assertTrue(path.is_file())

    def test_capability_emit_and_handoff(self) -> None:
        emit = run_imagine_generator_capability(
            {
                "action": "emit",
                "fixture": "scene-seed-demo",
                "runtime_context": "test_harness",
                "imagine_root": str(self.imagine_root),
                "ul_substrate": {"lane": "imagine"},
            }
        )
        self.assertTrue(emit["ok"])
        pattern = emit["pattern"]
        handoff = run_imagine_generator_capability(
            {
                "action": "handoff",
                "pattern": pattern,
                "runtime_context": "test_harness",
                "story_forge_root": str(self.story_forge_root),
            }
        )
        self.assertTrue(handoff["ok"])
        self.assertIn("ul_substrate", emit)


class TestImagineGeneratorAPI(unittest.TestCase):
    def test_emit_and_handoff_api(self) -> None:
        import src.api as api

        with api.app.test_client() as client:
            emit = client.post(
                "/api/jarvis/imagine/emit",
                json={"fixture": "scene-seed-demo"},
            )
            self.assertEqual(emit.status_code, 201)
            pattern = emit.get_json()["pattern"]
            handoff = client.post(
                "/api/jarvis/imagine/handoff",
                json={"pattern": pattern},
            )
            self.assertEqual(handoff.status_code, 200)
            self.assertEqual(handoff.get_json()["status"], "admitted")


if __name__ == "__main__":
    unittest.main()
