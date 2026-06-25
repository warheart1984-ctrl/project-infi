"""RLS conformance level checks."""

from __future__ import annotations

import os
from enum import IntEnum


class ConformanceLevel(IntEnum):
    L1 = 1
    L2 = 2
    L3 = 3


def configured_level() -> ConformanceLevel:
    raw = os.environ.get("RLS_CONFORMANCE_LEVEL", "1").strip()
    try:
        n = int(raw)
    except ValueError:
        n = 1
    if n >= 3:
        return ConformanceLevel.L3
    if n >= 2:
        return ConformanceLevel.L2
    return ConformanceLevel.L1


def assert_conformance_level(minimum: ConformanceLevel) -> None:
    current = configured_level()
    if current < minimum:
        raise AssertionError(
            f"RLS_CONFORMANCE_LEVEL={current.value} below required {minimum.value}"
        )
