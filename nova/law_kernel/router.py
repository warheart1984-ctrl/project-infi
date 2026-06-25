"""LawfulIntentRouter — no intent reaches substrate without LawKernel evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nova.law_kernel.context_resolver import LawContextResolver
from nova.law_kernel.kernel import LawKernel
from nova.law_kernel.law_ledger import LawLedger
from nova.law_kernel.lineage import LineageStore
from nova.law_kernel.models import Intent, LawDecision, LawEvalPayload, LineageContract
from nova.law_kernel.panic_handler import LawKernelPanicHandler
from nova.law_kernel.t5_binding import InvariantViolation
from nova.substrate.contracts import SubstrateRegistry


class LineageBindingError(ValueError):
    """Raised when lineage contract is not bound to the current T5 reference signal."""


class _LineageClient:
    def __init__(self, store: LineageStore) -> None:
        self._store = store

    def clear(self) -> None:
        self._store.clear()

    @property
    def events(self) -> list[dict[str, Any]]:
        return [event.to_dict() for event in self._store.list()]


class LineageEmitter:
    """Compatibility adapter for tests expecting lineage_emitter.client.events."""

    def __init__(self, store: LineageStore) -> None:
        self.client = _LineageClient(store)


@dataclass
class SubstrateExecutor:
    registry: SubstrateRegistry | None = None
    executed: list[Intent] = field(default_factory=list)
    denied: list[Intent] = field(default_factory=list)
    last_result: Any = None

    def execute(self, intent: Intent) -> Any:
        result = None
        if self.registry is not None and intent.payload.get("capability"):
            result = self.registry.execute(intent)
        self.last_result = result
        self.executed.append(intent)
        return result

    def deny(self, intent: Intent) -> None:
        self.denied.append(intent)


class LawfulIntentRouter:
    """KLAW-1: every action originates from a LawKernel-evaluated intent."""

    def __init__(
        self,
        *,
        kernel: LawKernel,
        context_resolver: LawContextResolver,
        lineage: LineageStore,
        panic_handler: LawKernelPanicHandler,
        lineage_contracts: dict[str, LineageContract] | None = None,
        substrate_registry: SubstrateRegistry | None = None,
    ) -> None:
        self.kernel = kernel
        self.context_resolver = context_resolver
        self.lineage = lineage
        self.lineage_emitter = LineageEmitter(lineage)
        self.panic_handler = panic_handler
        self.lineage_contracts = dict(lineage_contracts or context_resolver.lineage_contracts)
        self.substrate_registry = substrate_registry or SubstrateRegistry()
        self.substrate_executor = SubstrateExecutor(registry=self.substrate_registry)
        self.evaluations: list[LawEvalPayload] = []

    @property
    def ledger(self) -> LawLedger:
        return self.kernel.ledger

    def route(
        self,
        intent: Intent,
        *,
        actor_id: str,
        domain: str,
        epoch: str,
        lineage_contract_id: str,
        lineage_event_id: str = "",
    ) -> dict[str, Any]:
        if self.panic_handler.is_frozen(domain=domain, actor_id=actor_id):
            raise InvariantViolation(
                "LANE_FROZEN",
                details={"domain": domain, "actor_id": actor_id},
            )

        try:
            context = self.context_resolver.resolve(
                intent,
                actor_id=actor_id,
                domain=domain,
                epoch=epoch,
                lineage_contract_id=lineage_contract_id,
                lineage_event_id=lineage_event_id,
            )
        except InvariantViolation as exc:
            raise LineageBindingError(str(exc)) from exc

        evaluation = self.kernel.evaluate(context, intent)
        self.evaluations.append(evaluation)
        self.lineage.emit_law_eval(evaluation)

        if evaluation.decision == LawDecision.PANIC:
            self.panic_handler.handle(evaluation)
            return {
                "action": "PANIC",
                "admitted": False,
                "evaluation": evaluation.to_dict(),
            }

        if evaluation.decision == LawDecision.DENY:
            self.substrate_executor.deny(intent)
            return {
                "action": "DENY",
                "admitted": False,
                "evaluation": evaluation.to_dict(),
            }

        if evaluation.decision == LawDecision.TRANSFORM and evaluation.transformed_intent:
            self.substrate_executor.execute(evaluation.transformed_intent)
            pit_mode = str(intent.payload.get("pit_mode") or "")
            return {
                "action": pit_mode or "TRANSFORM",
                "admitted": True,
                "evaluation": evaluation.to_dict(),
            }

        self.substrate_executor.execute(intent)
        return {
            "action": "ADMIT",
            "admitted": True,
            "evaluation": evaluation.to_dict(),
        }
