"""ECK-2 Formation Engine — JPSS-F forward pipeline."""

from __future__ import annotations

from typing import Any

from constitutional.jpss.runtime import JPSSFormationRuntime
from constitutional.runtime.runtime import ConstitutionalStateRuntime


class ECK2FormationEngine:
    """Forward engine implementing JPSS-F."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self._runtime = JPSSFormationRuntime(csr)

    def run(self, steward_inputs: dict[str, Any]):
        return self._runtime.run(steward_inputs)
