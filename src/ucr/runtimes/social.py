"""SocialRuntime — tone and style shaping only."""

# Mythic: Social Continuity Membrane
# Engineering: SocialRuntime
from __future__ import annotations

from typing import Any

from src.ucr.runtime_base import CognitiveRuntime
from src.ucr.types import (
    CognitiveModeContract,
    CognitiveSituation,
    RuntimeConfig,
    RuntimeOutput,
    RuntimeTrace,
)

SOCIAL_RUNTIME_ID = "cognitive.social"


class SocialRuntime(CognitiveRuntime):
  """Shapes tone/style; does not alter governance or facts."""

  runtime_id = SOCIAL_RUNTIME_ID

  def __init__(self) -> None:
    self._config: RuntimeConfig | None = None
    self._tone = "professional"
    self._style = "concise"

  def describe_capabilities(self) -> dict[str, Any]:
    return {
      "runtime_id": self.runtime_id,
      "role": "social",
      "capabilities": ["tone_selection", "style_shaping"],
      "non_authoritative": True,
    }

  def accepts(self, contract: CognitiveModeContract) -> bool:
    return self.runtime_id in contract.required_runtimes or self.runtime_id in contract.optional_runtimes

  def configure(self, config: RuntimeConfig) -> None:
    self._config = config
    self._tone = str(config.params.get("tone") or self._tone)
    self._style = str(config.params.get("style") or self._style)

  def execute(self, situation: CognitiveSituation) -> RuntimeOutput:
    tone = str(situation.metadata.get("tone") or self._tone)
    style = str(situation.metadata.get("style") or self._style)
    return RuntimeOutput(
      runtime_id=self.runtime_id,
      status="ok",
      payload={
        "tone": tone,
        "style": style,
        "register": "operator_collaborative",
      },
    )

  def explain(self, output: RuntimeOutput) -> RuntimeTrace:
    return RuntimeTrace(
      runtime_id=self.runtime_id,
      summary=f"Applied tone={output.payload.get('tone')} style={output.payload.get('style')}",
      stages=("tone", "style"),
      evidence=dict(output.payload),
    )
