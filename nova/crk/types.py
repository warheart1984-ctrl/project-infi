"""CRK bridge types for cockpit and boundary panels."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class BoundaryStatus:
    status: Literal["stable", "warning", "violation"]
    violations: int
    message: str
    kernel: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status,
            "violations": self.violations,
            "message": self.message,
        }
        if self.kernel is not None:
            payload["kernel"] = self.kernel
        return payload
