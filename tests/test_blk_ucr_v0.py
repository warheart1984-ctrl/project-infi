"""Tests for BLK_UCR_V0 binary law key."""

from __future__ import annotations

import unittest

from src.ucr.binary_law_key import (
    CANONICAL_U128,
    BinaryLawKey,
    NonConformantLawKeyError,
    decode_priority,
    invariant_active,
    parse_and_validate,
    validate_law_key,
)


class BlkUcrV0Tests(unittest.TestCase):
    def test_canonical_parse(self) -> None:
        key = BinaryLawKey.parse(CANONICAL_U128)
        self.assertEqual(key.version, 0x01)
        self.assertEqual(key.layer_id, 0x02)
        self.assertEqual(key.priority_raw, 0x29CA)
        self.assertEqual(key.invariant_mask, 0xFF000000)
        self.assertEqual(key.reserved, 0x00000000)
        self.assertEqual(key.tag, 0x5532534F)

    def test_decode_priority(self) -> None:
        priority = decode_priority(0x29CA)
        self.assertEqual(priority["SAFE"], 0b001)
        self.assertEqual(priority["CONS"], 0b010)
        self.assertEqual(priority["UCR"], 0b011)
        self.assertEqual(priority["RT"], 0b100)
        self.assertEqual(priority["TURN"], 0b101)
        self.assertEqual(priority["PAD"], 0)

    def test_invariant_active(self) -> None:
        self.assertTrue(invariant_active(0xFF000000, 0))
        self.assertTrue(invariant_active(0xFF000000, 7))
        self.assertFalse(invariant_active(0x7F000000, 0))
        with self.assertRaises(ValueError):
            invariant_active(0xFF000000, 8)

    def test_validate_pass(self) -> None:
        result = validate_law_key(CANONICAL_U128)
        self.assertTrue(result.ok)

    def test_validate_fail_zero(self) -> None:
        result = validate_law_key(0)
        self.assertFalse(result.ok)

    def test_parse_and_validate_raises(self) -> None:
        with self.assertRaises(NonConformantLawKeyError):
            parse_and_validate(0)


if __name__ == "__main__":
    unittest.main()
