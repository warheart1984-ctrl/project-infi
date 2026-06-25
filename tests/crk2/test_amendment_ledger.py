"""Kernel amendment ledger tests."""

from __future__ import annotations

from src.kernel.amendment_ledger import InMemoryAmendmentStore, KernelAmendmentLedger


def test_ledger_appends_and_lists() -> None:
    store = InMemoryAmendmentStore()
    ledger = KernelAmendmentLedger(store)
    rec = ledger.append(
        kernel_version=1,
        insufficiency=0.72,
        signals=[0.1, 0.2, 0.3, 0.4, 0.5],
        reason="CRK-T2 insufficiency detected",
        ratified=False,
    )
    assert rec.id.startswith("KAM-")
    assert rec.ratified is False
    listed = ledger.list()
    assert len(listed) == 1
    assert listed[0].insufficiency == 0.72
