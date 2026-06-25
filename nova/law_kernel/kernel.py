"""LawKernel — evaluates applicable laws and returns LawEvalPayload."""

from __future__ import annotations

from nova.law_kernel.law_ledger import LawLedger
from nova.law_kernel.models import Intent, LawContext, LawDecision, LawEvalPayload, LawRecord, LawStatus
from nova.law_kernel.t5_binding import bind_law_eval_proof
from nova.law_kernel.transform import transform_intent


PIT_EVIDENCE_THRESHOLD = 0.8


class LawKernel:
    """Constitutional execution spine — admit, deny, transform, or panic."""

    def __init__(
        self,
        *,
        ledger: LawLedger,
        evidence_threshold: float = PIT_EVIDENCE_THRESHOLD,
    ) -> None:
        self.ledger = ledger
        self.evidence_threshold = evidence_threshold

    def applicable_laws(self, context: LawContext, intent: Intent) -> tuple[LawRecord, ...]:
        rows = [
            law
            for law in self.ledger.admitted()
            if law.status == LawStatus.ADMITTED and law.applies_to_domain(context.domain)
        ]
        pit_mode = str(intent.payload.get("pit_mode") or "").upper()
        if pit_mode in {"PIT-1", "PIT-2", "PIT-3"}:
            rows = [law for law in rows if law.code in {pit_mode, "UGR-C8"}]
        return tuple(rows)

    def _decide(
        self,
        context: LawContext,
        intent: Intent,
        laws: tuple[LawRecord, ...],
    ) -> tuple[LawDecision, tuple[str, ...]]:
        if not laws:
            return LawDecision.PANIC, ("No admitted laws available for context",)

        forbidden = [
            law
            for law in laws
            if f"FORBID DOMAIN:{context.domain.upper()}" in law.text.upper()
        ]
        if forbidden:
            return LawDecision.DENY, tuple(f"Forbidden by {law.code}" for law in forbidden)

        evidence_fitness = max(0.0, min(float(intent.payload.get("pit_evidence_fitness", 0.0)), 1.0))
        pit_mode = str(intent.payload.get("pit_mode", "PIT-1")).upper()
        pit_codes = {law.code for law in laws if law.code.startswith("PIT-")}

        if pit_mode in pit_codes and evidence_fitness >= self.evidence_threshold:
            return LawDecision.TRANSFORM, (
                f"PIT band active ({', '.join(sorted(pit_codes))}), evidence_fitness={evidence_fitness}",
            )

        return LawDecision.ADMIT, (f"Admitted under {', '.join(law.code for law in laws)}",)

    def evaluate(self, context: LawContext, intent: Intent) -> LawEvalPayload:
        laws = self.applicable_laws(context, intent)

        if str(intent.payload.get("force_panic") or "").lower() in {"1", "true", "yes"}:
            payload = self._build_payload(
                context,
                intent,
                laws,
                decision=LawDecision.PANIC,
                reasons=("KLAW-2: forced uncertainty panic",),
            )
            return self._attach_proof(payload)

        if str(intent.payload.get("force_deny") or "").lower() in {"1", "true", "yes"}:
            payload = self._build_payload(
                context,
                intent,
                laws,
                decision=LawDecision.DENY,
                reasons=("KLAW-2: explicit deny",),
            )
            return self._attach_proof(payload)

        decision, reasons = self._decide(context, intent, laws)
        transformed_intent = None
        if decision == LawDecision.TRANSFORM:
            transformed_intent = transform_intent(intent, context).transformed_intent

        payload = self._build_payload(
            context,
            intent,
            laws,
            decision=decision,
            reasons=reasons,
            transformed_intent=transformed_intent,
        )
        return self._attach_proof(payload)

    def _build_payload(
        self,
        context: LawContext,
        intent: Intent,
        laws: tuple[LawRecord, ...],
        *,
        decision: LawDecision,
        reasons: tuple[str, ...],
        transformed_intent: Intent | None = None,
    ) -> LawEvalPayload:
        return LawEvalPayload(
            context=context,
            candidate_intent=intent,
            applicable_laws=laws,
            decision=decision,
            reasons=reasons,
            t5_ref_signal_hash=context.t5_ref_signal_hash,
            invariant_proof_id="",
            transformed_intent=transformed_intent,
        )

    def _attach_proof(self, payload: LawEvalPayload) -> LawEvalPayload:
        proof = bind_law_eval_proof(payload.to_dict())
        return LawEvalPayload(
            context=payload.context,
            candidate_intent=payload.candidate_intent,
            applicable_laws=payload.applicable_laws,
            decision=payload.decision,
            reasons=payload.reasons,
            t5_ref_signal_hash=payload.t5_ref_signal_hash,
            invariant_proof_id=proof.id,
            transformed_intent=payload.transformed_intent,
        )
