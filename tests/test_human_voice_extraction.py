from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from src.capabilities.human_voice_extraction import run_human_voice_extraction_capability
from src.human_voice_extraction import (
    admit_speakers_constraints,
    apply_signoff,
    extract_from_fixture,
    extract_from_notes,
    persist_extraction,
    speakers_constraint_path,
    validate_extraction,
)
from src.phase_gate import reset_registry


class TestHumanVoiceExtraction(unittest.TestCase):
    def setUp(self) -> None:
        reset_registry()
        self.temp_root = Path(tempfile.mkdtemp(prefix="human_voice_test_"))
        self.extraction_root = self.temp_root / "human_voice"
        self.speakers_root = self.temp_root / "speakers"

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_extract_no_raw_source_in_pack(self) -> None:
        pack = extract_from_notes("Calm register. Pace is measured.")
        validate_extraction(pack)
        self.assertNotIn("notes_text", pack)
        self.assertFalse(pack["retention_policy"]["store_raw_source"])

    def test_fixture_traits(self) -> None:
        pack = extract_from_fixture("notes-demo-redacted")
        kinds = {t["trait_kind"] for t in pack["voice_profile"]["traits"]}
        self.assertIn("register", kinds)
        self.assertIn("pace", kinds)

    def test_handoff_blocked_without_signoff(self) -> None:
        pack = extract_from_fixture("notes-demo-redacted")
        result = admit_speakers_constraints(pack, speakers_root=self.speakers_root)
        self.assertEqual(result["status"], "rejected")

    def test_handoff_after_signoff(self) -> None:
        pack = extract_from_fixture("notes-demo-redacted")
        signed = apply_signoff(pack, "operator-test")
        persist_extraction(signed, root=self.extraction_root)
        result = admit_speakers_constraints(signed, speakers_root=self.speakers_root)
        self.assertEqual(result["status"], "admitted")
        path = speakers_constraint_path(signed["voice_profile"]["profile_id"], speakers_root=self.speakers_root)
        self.assertTrue(path.is_file())
        self.assertGreaterEqual(len(result["constraints"]["traits"]), 1)

    def test_capability_flow(self) -> None:
        extracted = run_human_voice_extraction_capability(
            {
                "action": "extract",
                "fixture": "notes-demo-redacted",
                "runtime_context": "test_harness",
                "extraction_root": str(self.extraction_root),
            }
        )
        self.assertTrue(extracted["ok"])
        pack = extracted["extraction"]
        signed = run_human_voice_extraction_capability(
            {
                "action": "signoff",
                "extraction": pack,
                "signoff_by": "operator",
                "runtime_context": "test_harness",
                "extraction_root": str(self.extraction_root),
            }
        )
        self.assertTrue(signed["ok"])
        handoff = run_human_voice_extraction_capability(
            {
                "action": "handoff",
                "extraction": signed["extraction"],
                "runtime_context": "test_harness",
                "speakers_root": str(self.speakers_root),
            }
        )
        self.assertTrue(handoff["ok"])


class TestHumanVoiceExtractionAPI(unittest.TestCase):
    def test_extract_signoff_handoff_api(self) -> None:
        import src.api as api

        with api.app.test_client() as client:
            extract = client.post(
                "/api/jarvis/human-voice/extract",
                json={"fixture": "notes-demo-redacted"},
            )
            self.assertEqual(extract.status_code, 201)
            pack = extract.get_json()["extraction"]
            blocked = client.post(
                "/api/jarvis/human-voice/handoff",
                json={"extraction": pack},
            )
            self.assertEqual(blocked.status_code, 400)
            signoff = client.post(
                "/api/jarvis/human-voice/signoff",
                json={"extraction": pack, "signoff_by": "operator"},
            )
            self.assertEqual(signoff.status_code, 200)
            signed = signoff.get_json()["extraction"]
            handoff = client.post(
                "/api/jarvis/human-voice/handoff",
                json={"extraction": signed},
            )
            self.assertEqual(handoff.status_code, 200)


if __name__ == "__main__":
    unittest.main()
