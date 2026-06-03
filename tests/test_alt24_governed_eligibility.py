#!/usr/bin/env python3
"""Smoke tests for Release 24 governed eligibility."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.governance.check_alt24_governed_eligibility import (  # noqa: E402
    ALT24_GENES,
    GOVERNED_PROOFS,
    check_eligibility,
)


def test_governed_proofs_exist():
    for gene in ALT24_GENES:
        assert GOVERNED_PROOFS[gene].is_file(), gene


def test_eligibility_no_missing_proofs():
    errors = [
        e
        for e in check_eligibility(ROOT)
        if "missing governed proof" in e or "missing genome" in e
    ]
    assert errors == []
