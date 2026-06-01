"""Tests for optional OCR/document vision helpers."""

import unittest

from src.document_vision import DocumentVision


class TestDocumentVision(unittest.TestCase):
    """Exercise OCR helper logic without requiring the OCR engine at test time."""

    def test_should_suggest_ocr_for_text_heavy_matches(self):
        """Text-like CLIP matches should make OCR look worthwhile."""
        self.assertTrue(
            DocumentVision.should_suggest_ocr(
                [
                    {"label": "text-heavy", "score": 0.22},
                    {"label": "screenshot", "score": 0.08},
                ]
            )
        )

    def test_describe_unavailable_returns_stable_payload(self):
        """Unavailable OCR should still serialize into a UI-friendly payload."""
        payload = DocumentVision().describe_unavailable(
            requested=True,
            top_matches=[{"label": "document", "score": 0.4}],
            message="Document vision is disabled for this deployment",
        )

        self.assertTrue(payload["requested"])
        self.assertEqual(payload["status"], "unavailable")
        self.assertTrue(payload["document_like"])
        self.assertIn("disabled", payload["summary"])


if __name__ == "__main__":
    unittest.main()
