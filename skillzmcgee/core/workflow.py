from __future__ import annotations

from collections.abc import Callable
from typing import Any

from skillzmcgee.core.adapters.llm_adapter import LawfulLLMAdapter
from skillzmcgee.core.receipts import build_receipt
from skillzmcgee.core.runner import SliceRunner
from skillzmcgee.governance.continuity_ledger import ValidatedLedger
from skillzmcgee.governance.state_accumulator import StateAccumulator


class Workflow:
    def __init__(
        self,
        *,
        ledger: ValidatedLedger,
        accumulator: StateAccumulator,
        actor: str = "skillz",
        llm: Callable[[str], str] | None = None,
    ) -> None:
        self.ledger = ledger
        self.accumulator = accumulator
        self.actor = actor
        self.runner = SliceRunner()
        self.llm_adapter = LawfulLLMAdapter(llm, ledger, accumulator, actor) if llm else None

    def run_slice(
        self,
        slice_id: str,
        payload: Any,
        slice_callable: Callable[[Any], Any],
    ) -> dict[str, Any]:
        try:
            output = self.runner.run(slice_callable, payload)
            receipt = build_receipt(
                actor=self.actor,
                slice_id=slice_id,
                input_data=payload,
                output_data=output,
                status="ok",
            )
        except Exception as exc:
            receipt = build_receipt(
                actor=self.actor,
                slice_id=slice_id,
                input_data=payload,
                output_data=None,
                status="error",
                error=str(exc),
            )
        self.ledger.append(receipt)
        self.accumulator.apply_entry(receipt)
        return receipt
