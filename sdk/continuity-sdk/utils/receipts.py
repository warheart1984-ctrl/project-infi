"""Receipt helpers — thin wrappers over CRK-1 validators."""

from __future__ import annotations

from typing import Any


def validate_crr1(receipt: dict[str, Any]) -> None:
    from src.crk1.crr1_validator import validate_crr1 as _validate

    _validate(receipt)


def validate_caa1(receipt: dict[str, Any]) -> None:
    from src.crk1.caa1_assimilation import validate_caa1 as _validate

    _validate(receipt)
