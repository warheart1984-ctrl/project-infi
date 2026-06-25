"""MemoryRuntime — facts and constraints retrieval."""

# Mythic: Hippocampus Runtime
# Engineering: MemoryRuntime
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

MEMORY_RUNTIME_ID = "cognitive.memory"


class MemoryRuntime(CognitiveRuntime):
  """Supplies bounded facts and constraints for the turn."""

  runtime_id = MEMORY_RUNTIME_ID

  def __init__(self, *, facts: dict[str, Any] | None = None) -> None:
    self._config: RuntimeConfig | None = None
    self._facts = dict(facts or {})

  def describe_capabilities(self) -> dict[str, Any]:
    return {
      "runtime_id": self.runtime_id,
      "role": "memory",
      "capabilities": ["fact_retrieval", "constraint_binding"],
      "accepts_modes": ("execute", "deliberate", "general", "recall"),
    }

  def accepts(self, contract: CognitiveModeContract) -> bool:
    return self.runtime_id in contract.required_runtimes or self.runtime_id in contract.optional_runtimes

  def configure(self, config: RuntimeConfig) -> None:
    self._config = config
    extra = config.params.get("facts")
    if isinstance(extra, dict):
      self._facts.update(extra)

  def execute(self, situation: CognitiveSituation) -> RuntimeOutput:
    session_facts = dict(self._facts)
    if situation.session_id:
      session_facts.setdefault("session_id", situation.session_id)
    constraints = list(situation.metadata.get("constraints") or [])
    constraints.append("governance_first")
    constraints.append("traceability_required")
    return RuntimeOutput(
      runtime_id=self.runtime_id,
      status="ok",
      payload={"facts": session_facts, "constraints": constraints},
    )

  def explain(self, output: RuntimeOutput) -> RuntimeTrace:
    fact_keys = list((output.payload.get("facts") or {}).keys())
    constraint_count = len(output.payload.get("constraints") or [])
    return RuntimeTrace(
      runtime_id=self.runtime_id,
      summary=f"Bound {len(fact_keys)} facts and {constraint_count} constraints",
      stages=("recall", "bind"),
      evidence={"fact_keys": fact_keys},
    )
