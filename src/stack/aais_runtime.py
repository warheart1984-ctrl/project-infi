"""AAIS — Governed Agent Runtime wrapping the base LLM."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable

from pydantic import BaseModel, Field

from src.continuity.ra.jpss_accumulation_sim import JPSSContributionEvent
from src.stack.crk1_api import CRK1Kernel, InvariantCheckResult
from src.stack.ra_cos1_api import RACOS1Layer


class LLMResponse(BaseModel):
    text: str
    model: str = "mock"
    tokens_used: int = 0


class LLMAdapter(ABC):
    @abstractmethod
    def complete(self, prompt: str, *, system: str = "") -> LLMResponse:
        ...


class MockLLMAdapter(LLMAdapter):
    """Deterministic LLM for vertical slice — no external API."""

    def complete(self, prompt: str, *, system: str = "") -> LLMResponse:
        prompt_lower = prompt.lower()
        if "task" in prompt_lower and "plan" in prompt_lower:
            text = (
                "Proposed plan: (1) capture current tasks, (2) identify dependencies, "
                "(3) assign owners without deleting existing task IDs."
            )
        elif "delete" in prompt_lower:
            text = "I cannot delete without explicit confirmation — preserving task IDs."
        else:
            text = f"Acknowledged: {prompt[:200]}"
        return LLMResponse(text=text, model="mock-governed", tokens_used=len(text.split()))


OperatorFn = Callable[..., Any]


class AAISRuntime:
    """
    Layer 1 — AAIS (Governed Agent Runtime).

    Wraps LLM in tool routing, capability boundaries, and policy checks via CRK-1.
    Emits JPSS contribution events into RA-COS-1.
    """

    def __init__(
        self,
        *,
        kernel: CRK1Kernel | None = None,
        continuity: RACOS1Layer | None = None,
        llm: LLMAdapter | None = None,
        actor_id: str = "aais-agent",
    ) -> None:
        self.kernel = kernel or CRK1Kernel()
        self.continuity = continuity or RACOS1Layer()
        self.llm = llm or MockLLMAdapter()
        self.actor_id = actor_id
        self._operators: dict[str, OperatorFn] = {}

    def register_operator(self, name: str, fn: OperatorFn) -> None:
        self._operators[name] = fn

    def _policy_check(self, intent: str) -> InvariantCheckResult:
        return self.kernel.check_invariant(actor_id=self.actor_id, intent=intent)

    def complete(
        self,
        prompt: str,
        *,
        system: str = "",
        emit_events: bool = True,
    ) -> tuple[LLMResponse, InvariantCheckResult]:
        """Run governed LLM completion with pre/post constitutional checks."""
        pre = self._policy_check(prompt)
        if not pre.allowed:
            blocked = LLMResponse(
                text=f"Request blocked by CRK-1: {'; '.join(pre.violations)}",
                model="blocked",
            )
            return blocked, pre

        if emit_events:
            self.continuity.log_observation(
                actor=self.actor_id,
                text=f"Request observed: {prompt[:200]}",
                phenomenon_anchor=prompt[:80],
            )

        response = self.llm.complete(prompt, system=system)

        post = self.kernel.block_output(response.text)
        if not post.allowed:
            blocked = LLMResponse(
                text=f"Output blocked by CRK-1: {'; '.join(post.violations)}",
                model="blocked",
            )
            return blocked, post

        if emit_events:
            interp = self.continuity.log_interpretation(
                actor=self.actor_id,
                text=response.text,
            )
            self.continuity.run_validation(interp.id)

        return response, post

    def invoke_operator(self, name: str, **kwargs: Any) -> Any:
        if name not in self._operators:
            raise KeyError(f"Unknown operator: {name}")
        pre = self._policy_check(f"invoke operator {name}")
        if not pre.allowed:
            raise PermissionError("; ".join(pre.violations))
        return self._operators[name](**kwargs)

    def last_events(self) -> list[JPSSContributionEvent]:
        return self.continuity.events
