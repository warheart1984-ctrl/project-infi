"""Test seams and runtime hooks for Nova governance."""

from __future__ import annotations

from nova.governance import ledger


def reset_seams_for_tests() -> None:
    """Reset test-visible governance state between pytest cases."""

    path = ledger.ledger_path()
    if path is not None and path.exists():
        path.unlink()
