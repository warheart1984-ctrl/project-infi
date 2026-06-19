"""Governance exceptions for the lawful Nova runtime."""

from __future__ import annotations


class GovernanceViolationError(Exception):
    """Raised when RSL, admission, or receipt checks fail."""

    def __init__(self, message: str, *, code: str = "GOVERNANCE-VIOLATION") -> None:
        super().__init__(message)
        self.code = code
