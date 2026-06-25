"""ECK-2 runtime — orchestrates formation, reconstruction, and continuity."""

from __future__ import annotations

from typing import Any

from constitutional.core.models import StateObject
from constitutional.eck2.kernel import ECK2Kernel
from constitutional.eck2.models import ECK2PipelineResult
from constitutional.runtime.runtime import ConstitutionalStateRuntime

ECK2_PIPELINE_STATE_ID = "eck2_pipeline__latest"


class ECK2Runtime:
    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr
        self._kernel = ECK2Kernel(csr)

    def run(self, steward_inputs: dict[str, Any]) -> ECK2PipelineResult:
        result = self._kernel.run(steward_inputs)
        self.csr.register_or_replace_state(
            StateObject(
                state_id=ECK2_PIPELINE_STATE_ID,
                state_type="eck2_pipeline",
                current_state="Observed",
            )
        )
        self.csr.put_domain_doc(ECK2_PIPELINE_STATE_ID, "eck2_pipeline", result)
        return result


def load_eck2_pipeline(csr: ConstitutionalStateRuntime) -> ECK2PipelineResult | None:
    try:
        doc = csr.get_domain_doc(ECK2_PIPELINE_STATE_ID, ECK2PipelineResult)
        assert isinstance(doc, ECK2PipelineResult)
        return doc
    except KeyError:
        return None
