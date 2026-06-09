"""Tests for OTEM capability level and authority bands."""

import os
import unittest

from src.otem_capability import (
    authority_band,
    capability_posture,
    get_otem_capability_level,
    is_ceiling_level,
    is_containment_band,
)


class TestOtemCapability(unittest.TestCase):
    def test_default_level_is_10(self):
        original = os.environ.pop("AAIS_OTEM_CAPABILITY_LEVEL", None)
        try:
            self.assertEqual(get_otem_capability_level(), 10)
            self.assertEqual(authority_band(10), "governed")
        finally:
            if original is not None:
                os.environ["AAIS_OTEM_CAPABILITY_LEVEL"] = original

    def test_level_5_is_autonomous(self):
        original = os.environ.get("AAIS_OTEM_CAPABILITY_LEVEL")
        os.environ["AAIS_OTEM_CAPABILITY_LEVEL"] = "5"
        try:
            self.assertEqual(get_otem_capability_level(), 5)
            self.assertEqual(authority_band(5), "autonomous")
            self.assertFalse(is_containment_band(5))
            self.assertFalse(is_ceiling_level(5))
        finally:
            if original is None:
                os.environ.pop("AAIS_OTEM_CAPABILITY_LEVEL", None)
            else:
                os.environ["AAIS_OTEM_CAPABILITY_LEVEL"] = original

    def test_containment_band_16_through_19(self):
        for level in (16, 17, 18, 19):
            self.assertEqual(authority_band(level), "containment")
            self.assertTrue(is_containment_band(level))
            self.assertFalse(is_ceiling_level(level))
            posture = capability_posture(level)
            self.assertEqual(posture.get("authority_band"), "containment")

    def test_sovereign_level_20(self):
        self.assertEqual(authority_band(20), "sovereign")
        self.assertFalse(is_containment_band(20))
        self.assertTrue(is_ceiling_level(20))
        posture = capability_posture(20)
        self.assertEqual(posture.get("authority_band"), "sovereign")


if __name__ == "__main__":
    unittest.main()
