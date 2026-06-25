"""Binary Law Key BLK_UCR_V0 — 128-bit governed law spine token."""

# Mythic: Binary Law Key
# Engineering: BinaryLawKey
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any

CANONICAL_U128 = 0x010229CAFF000000000000005532534F

VERSION_MASK = 0xFF000000000000000000000000000000
VERSION_SHIFT = 120
LAYER_MASK = 0x00FF0000000000000000000000000000
LAYER_SHIFT = 112
PRIORITY_MASK = 0x0000FFFF000000000000000000000000
PRIORITY_SHIFT = 96
INVARIANT_MASK = 0x00000000FFFFFFFF0000000000000000
INVARIANT_SHIFT = 64
RESERVED_MASK = 0x0000000000000000FFFFFFFF00000000
RESERVED_SHIFT = 32
TAG_MASK = 0x000000000000000000000000FFFFFFFF
TAG_SHIFT = 0

EXPECTED_VERSION = 0x01
EXPECTED_LAYER_ID = 0x02
EXPECTED_PRIORITY_RAW = 0x29CA
EXPECTED_INVARIANT_MASK = 0xFF000000
EXPECTED_RESERVED = 0x00000000
EXPECTED_TAG = 0x5532534F

PRIORITY_SAFE = 0b001
PRIORITY_CONS = 0b010
PRIORITY_UCR = 0b011
PRIORITY_RT = 0b100
PRIORITY_TURN = 0b101
PRIORITY_PAD = 0b0

UCR_INVARIANT_IDS = tuple(f"U{i}" for i in range(1, 9))


class LawTierId(IntEnum):
    SAFE = 1
    CONS = 2
    UCR = 3
    RT = 4
    TURN = 5


class NonConformantLawKeyError(ValueError):
    """Raised when a law key fails BLK_UCR_V0 validation."""


@dataclass(frozen=True, slots=True)
class LawKeyValidationResult:
    ok: bool
    reason_codes: tuple[str, ...] = ()
    fields: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class BinaryLawKey:
    """Parsed 128-bit BLK_UCR_V0 law key (big-endian, bit 127 = MSB)."""

    raw: int
    version: int
    layer_id: int
    priority_raw: int
    invariant_mask: int
    reserved: int
    tag: int

    @classmethod
    def parse(cls, law_key: int) -> BinaryLawKey:
        if law_key < 0 or law_key > (1 << 128) - 1:
            raise NonConformantLawKeyError("law_key must be a 128-bit unsigned integer")
        return cls(
            raw=law_key,
            version=(law_key & VERSION_MASK) >> VERSION_SHIFT,
            layer_id=(law_key & LAYER_MASK) >> LAYER_SHIFT,
            priority_raw=(law_key & PRIORITY_MASK) >> PRIORITY_SHIFT,
            invariant_mask=(law_key & INVARIANT_MASK) >> INVARIANT_SHIFT,
            reserved=(law_key & RESERVED_MASK) >> RESERVED_SHIFT,
            tag=(law_key & TAG_MASK) >> TAG_SHIFT,
        )

    def decode_priority(self) -> dict[str, int]:
        return decode_priority(self.priority_raw)

    def invariant_active(self, bit_index: int) -> bool:
        return invariant_active(self.invariant_mask, bit_index)

    def active_invariants(self) -> tuple[str, ...]:
        return tuple(
            invariant_id
            for index, invariant_id in enumerate(UCR_INVARIANT_IDS)
            if self.invariant_active(index)
        )

    def validate(self) -> LawKeyValidationResult:
        return validate_law_key(self.raw)

    def to_hex(self) -> str:
        return f"0x{self.raw:032X}"


def decode_priority(priority_raw: int) -> dict[str, int]:
    return {
        "SAFE": (priority_raw >> 13) & 0b111,
        "CONS": (priority_raw >> 10) & 0b111,
        "UCR": (priority_raw >> 7) & 0b111,
        "RT": (priority_raw >> 4) & 0b111,
        "TURN": (priority_raw >> 1) & 0b111,
        "PAD": priority_raw & 0b1,
    }


def invariant_active(mask: int, bit_index: int) -> bool:
    if bit_index < 0 or bit_index > 7:
        raise ValueError("bit_index must be 0..7 for U1..U8")
    return bool((mask >> (31 - bit_index)) & 1)


def validate_law_key(law_key: int) -> LawKeyValidationResult:
    reasons: list[str] = []
    if law_key == 0:
        reasons.append("LAW_KEY_ZERO")

    try:
        parsed = BinaryLawKey.parse(law_key)
    except NonConformantLawKeyError as exc:
        return LawKeyValidationResult(ok=False, reason_codes=(str(exc),))

    if parsed.version != EXPECTED_VERSION:
        reasons.append("VERSION_MISMATCH")
    if parsed.layer_id != EXPECTED_LAYER_ID:
        reasons.append("LAYER_MISMATCH")

    priority = decode_priority(parsed.priority_raw)
    if priority["SAFE"] != PRIORITY_SAFE:
        reasons.append("PRIORITY_SAFE_MISMATCH")
    if priority["CONS"] != PRIORITY_CONS:
        reasons.append("PRIORITY_CONS_MISMATCH")
    if priority["UCR"] != PRIORITY_UCR:
        reasons.append("PRIORITY_UCR_MISMATCH")
    if priority["RT"] != PRIORITY_RT:
        reasons.append("PRIORITY_RT_MISMATCH")
    if priority["TURN"] != PRIORITY_TURN:
        reasons.append("PRIORITY_TURN_MISMATCH")
    if priority["PAD"] != PRIORITY_PAD:
        reasons.append("PRIORITY_PAD_MISMATCH")

    if parsed.invariant_mask != EXPECTED_INVARIANT_MASK:
        reasons.append("INVARIANT_MASK_MISMATCH")
    if parsed.reserved != EXPECTED_RESERVED:
        reasons.append("RESERVED_NONZERO")
    if parsed.tag != EXPECTED_TAG:
        reasons.append("TAG_MISMATCH")

    return LawKeyValidationResult(
        ok=not reasons,
        reason_codes=tuple(reasons),
        fields={
            "version": parsed.version,
            "layer_id": parsed.layer_id,
            "priority": priority,
            "invariant_mask": parsed.invariant_mask,
            "reserved": parsed.reserved,
            "tag": parsed.tag,
            "active_invariants": parsed.active_invariants(),
        },
    )


def parse_and_validate(law_key: int) -> BinaryLawKey:
    result = validate_law_key(law_key)
    if not result.ok:
        raise NonConformantLawKeyError(
            f"BLK_UCR_V0 validation failed: {', '.join(result.reason_codes)}"
        )
    return BinaryLawKey.parse(law_key)


def validate_for_ul(law_key: int) -> bool:
    """UL admission gate — returns False when kernel must reject."""
    return validate_law_key(law_key).ok
