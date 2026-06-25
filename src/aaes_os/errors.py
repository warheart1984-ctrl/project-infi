"""AAES-OS validation errors with stable reason codes."""

from __future__ import annotations


class AaesOsValidationError(ValueError):
    """Raised when trace bus or reconstruction rejects an event or span."""

    def __init__(self, code: str, message: str) -> None:
        if not code or not str(code).strip():
            raise ValueError("code is required")
        if not message or not str(message).strip():
            raise ValueError("message is required")
        self.code = str(code).strip()
        super().__init__(f"{self.code}: {message}")
