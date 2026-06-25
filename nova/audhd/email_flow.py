"""AuDHD + UCC lawful email interaction orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from nova.audhd.interpreter import AuDHDInterpreter, Utterance
from nova.audhd.protection import AuDHDProtectionEngine, ProtectionFlags
from nova.audhd.safety_layer import AuDHDCognitiveSafetyLayer
from nova.cortex.facade import NovaCortexFacade
from nova.lineage.ucc_emit import emit_ucc_event
from nova.substrate.ucc_send_email import make_ucc_send_email_registry


DraftFn = Callable[[dict[str, Any]], str]


def _default_draft_reply(payload: dict[str, Any]) -> str:
    message = str(payload.get("message", ""))
    if "no" in message.lower() or "boundary" in message.lower():
        return (
            "I appreciate the opportunity, but I don't have the bandwidth to take this on right now. "
            "I want to make sure I can do high-quality work on my existing commitments."
        )
    return "Thank you for reaching out. I need a moment to review this and will follow up shortly."


@dataclass
class EmailFlowResult:
    incoming_interpreted: str
    protection_flags: ProtectionFlags
    protection_actions: dict[str, bool]
    draft_reply: str
    scaffolded_reply: str
    law_result: dict[str, Any] | None = None
    send_result: dict[str, Any] | None = None


@dataclass
class AuDHDEmailOrchestrator:
    protection: AuDHDProtectionEngine = field(default_factory=AuDHDProtectionEngine)
    interpreter: AuDHDInterpreter = field(default_factory=AuDHDInterpreter)
    safety: AuDHDCognitiveSafetyLayer = field(default_factory=AuDHDCognitiveSafetyLayer)
    cortex: NovaCortexFacade | None = None
    draft_fn: DraftFn = _default_draft_reply
    cognitive_style: str = "audhd"
    pacing_ok: bool = True

    def __post_init__(self) -> None:
        if self.cortex is None:
            self.cortex = NovaCortexFacade.from_kernel()

    def process_incoming(self, manager_email_text: str, *, intent: str = "request") -> tuple[str, ProtectionFlags, dict[str, bool]]:
        flags = self.protection.analyze(manager_email_text)
        actions = self.protection.apply(flags)
        utterance = Utterance(text=manager_email_text, tone="masked", intent=intent)
        audhd_view = self.interpreter.to_audhd(utterance)

        emit_ucc_event(
            kind="UCC_PROTECTION",
            actor_id="incoming",
            intent_id=None,
            cognitive_style=self.cognitive_style,
            overload_score=self.safety.state.overload_score,
            pacing_ok=self.pacing_ok,
            protection_flags=flags.to_dict(),
            interpreter_used=True,
        )

        return audhd_view, flags, actions

    def draft_response(
        self,
        user_text: str,
        *,
        audhd_view: str,
        flags: ProtectionFlags,
        actions: dict[str, bool],
        actor_id: str,
        epoch: str,
        lineage_contract_id: str,
    ) -> EmailFlowResult:
        self.safety.before_reply(user_text)

        payload = {
            "message": user_text,
            "task": "draft_boundary_email",
            "ucc_enabled": True,
            "cognitive_style": self.cognitive_style,
            "context": {
                "incoming_email_interpreted": audhd_view,
                "protection_flags": flags.to_dict(),
                "protection_actions": actions,
            },
            "pit_mode": "PIT-2",
            "pit_evidence_fitness": 0.9,
            "correctness_score": 0.9,
        }

        assert self.cortex is not None
        law_result = self.cortex.handle(
            kind="ASK",
            payload=payload,
            actor_id=actor_id,
            domain="cognition",
            epoch=epoch,
            lineage_contract_id=lineage_contract_id,
            lineage_event_id=f"le:{actor_id}:draft",
        )

        raw_reply = self.draft_fn(payload)
        scaffolded = self.safety.scaffold_reply(
            raw_reply if not self.safety.should_chunk() else raw_reply[:300],
            for_external=False,
        )

        emit_ucc_event(
            kind="UCC_INTERACTION",
            actor_id=actor_id,
            intent_id=law_result.get("evaluation", {}).get("candidate_intent", {}).get("id"),
            cognitive_style=self.cognitive_style,
            overload_score=self.safety.state.overload_score,
            pacing_ok=self.pacing_ok,
            protection_flags=flags.to_dict(),
            interpreter_used=True,
        )

        return EmailFlowResult(
            incoming_interpreted=audhd_view,
            protection_flags=flags,
            protection_actions=actions,
            draft_reply=raw_reply,
            scaffolded_reply=scaffolded,
            law_result=law_result,
        )

    def send_response(
        self,
        *,
        manager_email: str,
        body: str,
        actor_id: str,
        epoch: str,
        lineage_contract_id: str,
    ) -> dict[str, Any]:
        assert self.cortex is not None

        confirm_payload = {
            "message": "confirm send email",
            "task": "confirm_send_email",
            "tool_args": {
                "to": manager_email,
                "subject": "Re: Project request",
                "body": body,
            },
            "pit_mode": "PIT-3",
            "pit_evidence_fitness": 0.85,
            "correctness_score": 0.9,
            "ucc_enabled": True,
            "cognitive_style": self.cognitive_style,
        }

        law_result = self.cortex.handle(
            kind="ASK",
            payload=confirm_payload,
            actor_id=actor_id,
            domain="planning",
            epoch=epoch,
            lineage_contract_id=lineage_contract_id,
            lineage_event_id=f"le:{actor_id}:send",
        )

        from nova.law_kernel.models import new_intent

        send_payload = {
            "capability": "send_email",
            "tool_args": {
                "to": manager_email,
                "subject": "Re: Project request",
                "body": body,
            },
        }
        intent = new_intent(kind="ACT", payload=send_payload, origin=actor_id)
        ucc_registry = make_ucc_send_email_registry()
        try:
            substrate_result = ucc_registry.execute(
                intent,
                overload_score=self.safety.state.overload_score,
                pacing_ok=self.pacing_ok,
                cognitive_style=self.cognitive_style,
            )
        except RuntimeError as exc:
            emit_ucc_event(
                kind="UCC_CAPABILITY_BLOCKED",
                actor_id=actor_id,
                intent_id=intent.id,
                cognitive_style=self.cognitive_style,
                overload_score=self.safety.state.overload_score,
                pacing_ok=self.pacing_ok,
                capability="send_email",
            )
            return {"law_result": law_result, "error": str(exc), "sent": False}

        return {"law_result": law_result, "substrate_result": substrate_result, "sent": True}
