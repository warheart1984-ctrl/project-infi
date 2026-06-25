"""SafetyRuntime — veto gate; always accepts activation."""

# Mythic: Safety Membrane
# Engineering: SafetyRuntime
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
    SafetyVerdict,
)

SAFETY_RUNTIME_ID = "cognitive.safety"

_UNSAFE_MARKERS = frozenset(
  {
    "destructive_reset",
    "wipe_all",
    "override_governance",
    "bypass_policy",
    "force_invariant_block",
  }
)


class SafetyRuntime(CognitiveRuntime):
  """Veto-capable runtime; evaluates safety before merge."""

  runtime_id = SAFETY_RUNTIME_ID

  def __init__(self) -> None:
    self._config: RuntimeConfig | None = None
    self._force_unsafe: bool = False

  def describe_capabilities(self) -> dict[str, Any]:
    return {
      "runtime_id": self.runtime_id,
      "role": "veto",
      "capabilities": ["safety_screen", "policy_veto"],
      "always_accepts": True,
      "veto_capable": True,
    }

  def accepts(self, contract: CognitiveModeContract) -> bool:
    return True

  def configure(self, config: RuntimeConfig) -> None:
    self._config = config
    self._force_unsafe = bool(config.params.get("force_unsafe"))

  def execute(self, situation: CognitiveSituation) -> RuntimeOutput:
    markers = set(situation.metadata.get("unsafe_markers") or [])
    meta_text = " ".join(str(v) for v in situation.metadata.values()).lower()
    operation = str(situation.metadata.get("operation") or "").lower()

    unsafe = (
      self._force_unsafe
      or situation.risk_profile == RiskProfile.CRITICAL
      or markers & _UNSAFE_MARKERS
      or operation in _UNSAFE_MARKERS
      or any(marker in meta_text for marker in _UNSAFE_MARKERS)
    )

    verdict = SafetyVerdict.UNSAFE if unsafe else SafetyVerdict.SAFE
    return RuntimeOutput(
      runtime_id=self.runtime_id,
      status="ok",
      payload={"verdict": verdict.value, "screened_input": situation.normalized_input[:200]},
      veto=unsafe,
      veto_reason="safety_screen_failed" if unsafe else None,
    )

  def explain(self, output: RuntimeOutput) -> RuntimeTrace:
    verdict = output.payload.get("verdict", "unknown")
    return RuntimeTrace(
      runtime_id=self.runtime_id,
      summary=f"Safety verdict: {verdict}",
      stages=("screen",),
      evidence={"veto": output.veto, "veto_reason": output.veto_reason},
    )
