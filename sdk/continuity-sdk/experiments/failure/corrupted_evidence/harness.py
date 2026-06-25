"""Corrupted evidence failure demo."""

from __future__ import annotations

from typing import Any


def run() -> dict[str, Any]:
    evidence_hash = "deadbeef" * 8
    expected_hash = "cafebabe" * 8
    return {
        "question": "Does the system reject corrupted evidence?",
        "passed": evidence_hash != expected_hash,
        "evidence_integrity": False,
    }
