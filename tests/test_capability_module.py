"""Tests for the AAIS capability-module base contract."""

import unittest

from src.capability_module import (
    AAISDocumentCapabilityModule,
    AAISImageCapabilityModule,
    AAISMusicCapabilityModule,
)


class TestCapabilityModule(unittest.TestCase):
    """Verify deterministic success and failure shapes across module types."""

    def test_image_module_returns_normalized_success_object(self):
        module = AAISImageCapabilityModule(
            provider_name="mock_image",
            handlers={
                "analyze": lambda payload: {
                    "summary": f"Analyzed {payload['source']}",
                    "labels": ["diagram", "ui"],
                }
            },
        )

        result = module.execute("analyze", {"source": "mock://image.png"})

        self.assertTrue(result["ok"])
        self.assertEqual(result["module"], "image")
        self.assertEqual(result["action"], "analyze")
        self.assertEqual(result["data"]["summary"], "Analyzed mock://image.png")
        self.assertEqual(result["meta"]["provider"], "mock_image")
        self.assertIn("trace_id", result["meta"])
        self.assertEqual(result["meta"]["result_size"], 2)

    def test_music_module_maps_timeout_to_deterministic_error(self):
        module = AAISMusicCapabilityModule(
            provider_name="mock_music",
            handlers={
                "detect_bpm": lambda payload: (_ for _ in ()).throw(TimeoutError("provider timed out"))
            },
        )

        result = module.execute("detect_bpm", {"source": "track.wav"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["module"], "music")
        self.assertEqual(result["action"], "detect_bpm")
        self.assertEqual(result["error_type"], "TimeoutError")
        self.assertEqual(result["details"]["provider"], "mock_music")
        self.assertEqual(result["details"]["stage"], "execute")

    def test_document_module_blocks_semantically_invalid_result(self):
        module = AAISDocumentCapabilityModule(
            provider_name="mock_document",
            handlers={"extract_fields": lambda payload: {"summary": "wrong shape"}},
        )

        result = module.execute("extract_fields", {"source": "contract.pdf"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["module"], "document")
        self.assertEqual(result["action"], "extract_fields")
        self.assertEqual(result["error_type"], "SemanticError")
        self.assertIn("Missing required fields", result["message"])
