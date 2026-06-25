"""Alias module — `nova.law_kernel.ledger` re-exports LawLedger."""

from nova.law_kernel.law_ledger import LawLedger, LawLedgerImmutableError

__all__ = ["LawLedger", "LawLedgerImmutableError"]
