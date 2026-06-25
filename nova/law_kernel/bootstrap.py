"""Bootstrap Nova Law Kernel v1.0 stack for tests and local dev."""

from __future__ import annotations

from nova.law_kernel import t5_binding
from nova.law_kernel.context_resolver import LawContextResolver
from nova.law_kernel.kernel import LawKernel
from nova.law_kernel.law_ledger import LawLedger
from nova.law_kernel.lineage import LineageStore
from nova.law_kernel.models import LawStatus, LineageContract
from nova.law_kernel.panic_handler import LawKernelPanicHandler
from nova.law_kernel.router import LawfulIntentRouter
from nova.law_kernel.t5_binding import InvariantLedger
from nova.substrate.contracts import CapabilityContract, SubstrateRegistry


def _seed_founding_laws(ledger: LawLedger) -> None:
    ledger.add_law(
        code="PIT-1",
        text="Capability evolution transforms MAY be applied when evidence fitness is high.",
        status=LawStatus.ADMITTED,
        fitness=1.0,
        epoch="EPOCH:0:T0",
        domains=["cognition", "governance", "planning"],
    )
    ledger.add_law(
        code="PIT-2",
        text="Self-reflection transforms MAY be applied to increase transparency and correctness.",
        status=LawStatus.ADMITTED,
        fitness=0.85,
        epoch="EPOCH:0:T0",
        domains=["cognition", "governance"],
    )
    ledger.add_law(
        code="PIT-3",
        text="Multi-step planning transforms MAY be applied when plans are lineage-anchored and evaluated.",
        status=LawStatus.ADMITTED,
        fitness=0.83,
        epoch="EPOCH:0:T0",
        domains=["planning", "cognition"],
    )
    ledger.add_law(
        code="UGR-C8",
        text="Lawful Creation Invariant",
        status=LawStatus.ADMITTED,
        fitness=1.0,
        epoch="EPOCH:0:T0",
    )
    for code, text in (
        (
            "LAW-UCC-1",
            "Nova must not privilege one cognitive style over another. All interaction patterns must support both linear and AuDHD cognition.",
        ),
        (
            "LAW-UCC-2",
            "All expectations, transitions, and boundaries must be explicit. Implicit demands are prohibited.",
        ),
        (
            "LAW-UCC-3",
            "Nova must ask for pacing preference before delivering multi-step or high-density information.",
        ),
        (
            "LAW-UCC-4",
            "If overload_score >= threshold: Nova must reduce output length, increase structure, and offer pause.",
        ),
        (
            "LAW-UCC-5",
            "When ambiguity is detected in incoming communication: Nova must translate it into explicit intent before presenting it to the user.",
        ),
        (
            "LAW-UCC-6",
            "Nova must support user boundaries and prevent coercive or manipulative patterns.",
        ),
    ):
        ledger.add_law(
            code=code,
            text=text,
            status=LawStatus.ADMITTED,
            fitness=1.0,
            epoch="EPOCH:0:T0",
            domains=["cognition", "governance", "substrate"],
        )


def _default_substrate_registry() -> SubstrateRegistry:
    registry = SubstrateRegistry()

    def _echo_handler(intent):
        return {"status": "ok", "intent_id": intent.id}

    registry.register(
        CapabilityContract(
            name="tool_call",
            handler=_echo_handler,
            invariants={
                "has_tool_name": lambda i: bool(i.payload.get("tool_name")),
            },
        )
    )
    registry.register(
        CapabilityContract(
            name="echo",
            handler=_echo_handler,
            invariants={},
        )
    )
    return registry


def make_law_kernel_stack(*, persist: bool = True) -> LawfulIntentRouter:
    InvariantLedger.reset()
    ref = t5_binding.T5ReferenceSignal.current()
    contracts = {
        "lc-1": LineageContract(
            id="lc-1",
            subject="operator-default",
            current_ref_signal_hash=ref.hash,
        ),
        "lc-omega": LineageContract(
            id="lc-omega",
            subject="omega",
            current_ref_signal_hash=ref.hash,
        ),
    }
    lineage = LineageStore()
    ledger = LawLedger(persist=persist)
    if not ledger.all():
        _seed_founding_laws(ledger)
    resolver = LawContextResolver(lineage_contracts=contracts)
    kernel = LawKernel(ledger=ledger)
    panic_handler = LawKernelPanicHandler(lineage=lineage)
    return LawfulIntentRouter(
        kernel=kernel,
        context_resolver=resolver,
        lineage=lineage,
        panic_handler=panic_handler,
        lineage_contracts=contracts,
        substrate_registry=_default_substrate_registry(),
    )
