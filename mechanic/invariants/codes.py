"""GOV / RNT / CST / HUM diagnostic code helpers."""

from __future__ import annotations

from typing import Any, Literal

DiagnosticFamily = Literal["GOV", "RNT", "CST", "HUM"]

FAMILIES: frozenset[str] = frozenset({"GOV", "RNT", "CST", "HUM"})


def parse_code(code: str) -> tuple[str, str]:
    """Return (family, numeric_suffix) e.g. GOV-12 -> (GOV, 12)."""
    text = str(code or "").strip().upper()
    if "-" not in text:
        return "", text
    family, suffix = text.split("-", 1)
    return family, suffix


def format_drift(
    *,
    code: str,
    summary: str,
    evidence: dict[str, Any],
    ma13_class: str = "",
    severity: str = "medium",
) -> dict[str, Any]:
    family, _ = parse_code(code)
    return {
        "code": code,
        "family": family,
        "invariant_id": code,
        "drift_detected": True,
        "drift_summary": summary,
        "severity": severity,
        "ma13_class": ma13_class,
        "evidence": evidence,
    }
