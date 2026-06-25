"""Nova Law Kernel v1.0 integration tests."""

from __future__ import annotations

import pytest

from nova.law_kernel.bootstrap import make_law_kernel_stack
from nova.law_kernel.law_ledger import LawLedger, LawLedgerImmutableError
from nova.law_kernel.models import LawDecision, LawStatus, new_intent, new_law_record
from nova.law_kernel.t5_binding import T5ReferenceSignal


class _TestRef(T5ReferenceSignal):
    @classmethod
    def current(cls) -> T5ReferenceSignal:
        return T5ReferenceSignal(
            id="t5-test",
            hash="ref-hash-test",
            issued_at="now",
            issuer="test",
        )


@pytest.fixture
def router(monkeypatch):
    monkeypatch.setattr("nova.law_kernel.t5_binding.T5ReferenceSignal", _TestRef)
    return make_law_kernel_stack()


def test_klaw1_no_ungoverned_action(router) -> None:
    intent = new_intent(kind="ASK", payload={}, origin="operator")
    router.route(
        intent,
        actor_id="actor-1",
        domain="cognition",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
    )
    assert router.evaluations
    assert router.lineage.list()
    assert router.substrate_executor.executed


def test_klaw3_append_only_ledger() -> None:
    ledger = LawLedger()
    row = new_law_record(code="SIT-1", text="structural integrity")
    ledger.append(row)
    with pytest.raises(LawLedgerImmutableError):
        ledger.append(row)


def test_klaw4_reference_anchored_eval(router) -> None:
    intent = new_intent(kind="ASK", payload={}, origin="operator")
    router.route(
        intent,
        actor_id="actor-1",
        domain="cognition",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
    )
    evaluation = router.evaluations[-1]
    assert evaluation.t5_ref_signal_hash == "ref-hash-test"
    assert evaluation.invariant_proof_id


def test_klaw2_panic_freezes_lane(router) -> None:
    intent = new_intent(kind="ASK", payload={"force_panic": True}, origin="operator")
    result = router.route(
        intent,
        actor_id="actor-1",
        domain="cognition",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
    )
    assert result["action"] == "PANIC"
    assert router.panic_handler.is_frozen(domain="cognition", actor_id="actor-1")
    assert any(event.kind == "LAW_PANIC" for event in router.lineage.list())


def test_klaw2_deny_path(router) -> None:
    intent = new_intent(kind="ASK", payload={"force_deny": True}, origin="operator")
    result = router.route(
        intent,
        actor_id="actor-1",
        domain="cognition",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
    )
    assert result["action"] == "DENY"
    assert router.substrate_executor.denied
    assert not router.substrate_executor.executed


def test_law_eval_emits_lineage_event(router) -> None:
    intent = new_intent(kind="ASK", payload={}, origin="operator")
    router.route(
        intent,
        actor_id="actor-1",
        domain="io",
        epoch="EPOCH:0:T0",
        lineage_contract_id="lc-1",
    )
    events = router.lineage.list()
    assert events[-1].kind == "LAW_EVAL"
    assert events[-1].ref_signal_hash == "ref-hash-test"
    assert router.evaluations[-1].decision == LawDecision.ADMIT
