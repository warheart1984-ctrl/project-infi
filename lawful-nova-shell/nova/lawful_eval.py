"""Small evaluation harness for the lawful Nova runtime."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable

from nova.exceptions import GovernanceViolationError
from nova.lawful_llm import LawfulLLM


@dataclass(frozen=True)
class LawfulEvalCase:
    name: str
    prompt: str
    tenant_id: str
    capability: str
    must_contain: tuple[str, ...] = ()
    must_not_contain: tuple[str, ...] = ()
    expected_receipt_fields: tuple[str, ...] = ()
    expect_rejection_code: str | None = None


def run_lawful_eval_suite(
    llm: LawfulLLM,
    cases: Iterable[LawfulEvalCase],
) -> dict:
    """Run deterministic checks for grounding, refusal, memory, and receipts."""

    results = []
    for case in cases:
        checks: list[str] = []
        try:
            turn = llm.ask(case.prompt, tenant_id=case.tenant_id, capability=case.capability)
        except GovernanceViolationError as exc:
            passed = exc.code == case.expect_rejection_code
            results.append(
                {
                    "name": case.name,
                    "passed": passed,
                    "checks": [f"rejection:{exc.code}"],
                    "error_code": exc.code,
                }
            )
            continue

        text = turn.text
        receipt = turn.receipt
        receipt_payload = json.loads(receipt["payload"])
        for needle in case.must_contain:
            checks.append(f"contains:{needle}")
            if needle not in text:
                results.append(_failed(case.name, checks, receipt, f"missing {needle!r}"))
                break
        else:
            for needle in case.must_not_contain:
                checks.append(f"not_contains:{needle}")
                if needle in text:
                    results.append(_failed(case.name, checks, receipt, f"unexpected {needle!r}"))
                    break
            else:
                for field in case.expected_receipt_fields:
                    checks.append(f"receipt_field:{field}")
                    if field not in receipt_payload:
                        results.append(_failed(case.name, checks, receipt, f"missing receipt {field!r}"))
                        break
                else:
                    results.append(
                        {
                            "name": case.name,
                            "passed": case.expect_rejection_code is None,
                            "checks": checks,
                            "receipt": receipt,
                        }
                    )

    passed = sum(1 for result in results if result["passed"])
    total = len(results)
    return {
        "suite": "nova_lawful_eval.v1",
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "cases": results,
    }


def _failed(name: str, checks: list[str], receipt: dict, reason: str) -> dict:
    return {
        "name": name,
        "passed": False,
        "checks": checks,
        "reason": reason,
        "receipt": receipt,
    }
