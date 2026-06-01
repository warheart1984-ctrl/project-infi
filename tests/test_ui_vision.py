"""Tests for optional screenshot and UI understanding helpers."""

import os
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from src.ui_vision import UIVision


class TestUIVision(unittest.TestCase):
    """Exercise lightweight screenshot/UI heuristics without extra deps."""

    def _make_screenshot_like_image(self):
        image = Image.new("RGB", (1440, 900), color="#0f1720")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 1440, 84), fill="#111827")
        draw.rectangle((0, 84, 240, 900), fill="#1f2937")
        draw.rectangle((280, 150, 680, 360), fill="#f8fafc")
        draw.rectangle((720, 150, 1160, 520), fill="#e2e8f0")
        draw.rectangle((280, 420, 1160, 760), fill="#111827")
        return image

    def test_should_suggest_ui_for_screenshotish_matches(self):
        """Screenshot-heavy CLIP matches should trigger deeper UI analysis."""
        self.assertTrue(
            UIVision.should_suggest_ui(
                [
                    {"label": "screenshot", "score": 0.14},
                    {"label": "text-heavy", "score": 0.09},
                ]
            )
        )

    def test_analyze_returns_structured_ui_payload_when_enabled(self):
        """Enabled UI vision should summarize surface type, layout, and theme."""
        image = self._make_screenshot_like_image()

        with patch.dict(os.environ, {"AAIS_ENABLE_UI_VISION": "1"}, clear=False):
            payload = UIVision().analyze(
                image,
                top_matches=[
                    {"label": "screenshot", "score": 0.31},
                    {"label": "text-heavy", "score": 0.18},
                ],
                ocr_result={
                    "text_preview": "Dashboard\nSettings\nActivity Feed\nRevenue",
                    "document_like": True,
                },
            )

        self.assertEqual(payload["status"], "available")
        self.assertEqual(payload["platform_hint"], "desktop")
        self.assertEqual(payload["theme"], "dark")
        self.assertIn(payload["surface_type"], {"ui_screenshot", "dashboard_or_chart"})
        self.assertGreaterEqual(payload["panel_estimate"], 2)
        self.assertTrue(payload["layout_clues"])

    def test_describe_unavailable_is_ui_friendly(self):
        """Unavailable UI understanding should still serialize into a stable payload."""
        payload = UIVision().describe_unavailable(
            requested=True,
            top_matches=[{"label": "screenshot", "score": 0.4}],
            message="UI understanding is disabled for this deployment",
        )

        self.assertTrue(payload["requested"])
        self.assertEqual(payload["status"], "unavailable")
        self.assertTrue(payload["document_like"])
        self.assertIn("disabled", payload["summary"])


if __name__ == "__main__":
    unittest.main()
