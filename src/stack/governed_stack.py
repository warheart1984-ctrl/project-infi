"""Governed stack — Human → CRK-1 → RA-COS-1 → AAIS → LLM → … → Human."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.stack.aais_runtime import AAISRuntime, LLMResponse
from src.stack.crk1_api import CRK1Kernel, ConstitutionalSnapshot, InvariantCheckResult
from src.stack.ra_cos1_api import ContinuityHealth, RACOS1Layer


class GovernedStackRequest(BaseModel):
    actor_id: str = "human-operator"
    prompt: str
    system: str = ""


class GovernedStackResponse(BaseModel):
    allowed: bool
    response_text: str
    constitutional_check: InvariantCheckResult
    health: ContinuityHealth
    call_chain: list[str] = Field(default_factory=list)
    blocked_reason: str | None = None


class GovernedStack:
    """
    Full collapsed stack call path:

    Human → CRK-1 → RA-COS-1 → AAIS → LLM → AAIS → RA-COS-1 → CRK-1 → Human
    """

    def __init__(
        self,
        *,
        kernel: CRK1Kernel | None = None,
        continuity: RACOS1Layer | None = None,
        aais: AAISRuntime | None = None,
    ) -> None:
        self.kernel = kernel or CRK1Kernel()
        self.continuity = continuity or RACOS1Layer()
        self.aais = aais or AAISRuntime(kernel=self.kernel, continuity=self.continuity)

    def get_constitution(self) -> ConstitutionalSnapshot:
        return self.kernel.get_constitution()

    def handle_request(self, request: GovernedStackRequest) -> GovernedStackResponse:
        chain: list[str] = ["Human → CRK-1"]

        pre = self.kernel.check_invariant(
            actor_id=request.actor_id,
            intent=request.prompt,
        )
        if not pre.allowed:
            return GovernedStackResponse(
                allowed=False,
                response_text="",
                constitutional_check=pre,
                health=self.continuity.get_continuity_health(),
                call_chain=chain + ["CRK-1 BLOCK"],
                blocked_reason="; ".join(pre.violations),
            )

        chain.extend(["CRK-1 → RA-COS-1", "RA-COS-1 → AAIS", "AAIS → LLM"])

        llm_response, post_check = self.aais.complete(
            request.prompt,
            system=request.system,
        )

        chain.extend(["LLM → AAIS", "AAIS → RA-COS-1 (I/V events)", "RA-COS-1 → CRK-1", "CRK-1 → Human"])

        health = self.continuity.get_continuity_health()

        return GovernedStackResponse(
            allowed=post_check.allowed,
            response_text=llm_response.text,
            constitutional_check=post_check,
            health=health,
            call_chain=chain,
            blocked_reason=None if post_check.allowed else "; ".join(post_check.violations),
        )

    def get_health(self) -> ContinuityHealth:
        return self.continuity.get_continuity_health()
