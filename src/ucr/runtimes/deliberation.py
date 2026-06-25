"""DeliberationRuntime — option generation and tradeoff framing."""

# Mythic: Deliberation Lobe
# Engineering: DeliberationRuntime
from __future__ import annotations

from typing import Any

from src.ucr.runtime_base import CognitiveRuntime
from src.ucr.types import (
    CognitiveModeContract,
    CognitiveSituation,
    RiskProfile,
    RuntimeConfig,
    RuntimeOutput,
    RuntimeTrace,
)

DELIBERATION_RUNTIME_ID = "cognitive.deliberation"


class DeliberationRuntime(CognitiveRuntime):
  """Primary runtime: generates bounded options for operator decisions."""

  runtime_id = DELIBERATION_RUNTIME_ID

  def __init__(self) -> None:
    self._config: RuntimeConfig | None = None

  def describe_capabilities(self) -> dict[str, Any]:
    return {
      "runtime_id": self.runtime_id,
      "role": "primary",
      "capabilities": ["option_generation", "tradeoff_framing", "intent_alignment"],
      "accepts_modes": ("deliberate", "execute", "general"),
      "refuses_risk": [RiskProfile.CRITICAL.value],
    }

  def accepts(self, contract: CognitiveModeContract) -> bool:
    if contract.risk_profile == RiskProfile.CRITICAL:
      return False
    return self.runtime_id in contract.required_runtimes or self.runtime_id in contract.optional_runtimes

  def configure(self, config: RuntimeConfig) -> None:
    self._config = config

  def execute(self, situation: CognitiveSituation) -> RuntimeOutput:
    if situation.risk_profile == RiskProfile.CRITICAL:
      return RuntimeOutput(
        runtime_id=self.runtime_id,
        status="refused",
        payload={"reason": "critical risk_profile — deliberation deferred to governance"},
      )

    options = [
      {"id": "opt_a", "label": f"Proceed with: {situation.normalized_input[:80]}"},
      {"id": "opt_b", "label": "Request clarification before acting"},
      {"id": "opt_c", "label": "Defer to operator review"},
    ]
    return RuntimeOutput(
      runtime_id=self.runtime_id,
      status="ok",
      payload={
        "options": options,
        "recommended": "opt_a",
        "intent_hint": situation.intent_hint,
      },
    )

  def explain(self, output: RuntimeOutput) -> RuntimeTrace:
    option_count = len(output.payload.get("options") or [])
    return RuntimeTrace(
      runtime_id=self.runtime_id,
      summary=f"Generated {option_count} bounded options",
      stages=("options", "tradeoffs"),
      evidence={"status": output.status, "recommended": output.payload.get("recommended")},
    )
