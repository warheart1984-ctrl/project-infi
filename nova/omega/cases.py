from __future__ import annotations

from copy import deepcopy
from typing import Any

from nova.law_kernel.capability_ladders import DOMAIN_LADDERS, GLOBAL_CAPABILITY_HARD_CAP
from nova.law_kernel.models import LawStatus
from nova.omega.harness import OmegaCase


def case_bad_domain() -> OmegaCase:
    def mutate(router: Any) -> None:
        for code in ("PIT-2", "PIT-3"):
            if router.ledger.get(code) is not None:
                router.ledger.append_status_change(
                    code,
                    status=LawStatus.REVOKED,
                    epoch="EPOCH:OMEGA",
                )
        router.ledger.add_law(
            code="PIT-2-BAD",
            text="Self-reflection transforms MAY be applied in BADDOMAIN only.",
            status=LawStatus.ADMITTED,
            fitness=0.9,
            epoch="EPOCH:OMEGA",
            domains=["BADDOMAIN"],
        )

    def expect(events: list[dict[str, Any]], _router: Any) -> bool:
        for event in events:
            if event["kind"] == "LAW_EVAL" and event["payload"]["decision"] == "transform":
                return False
        return True

    return OmegaCase(
        name="PIT-2 wrong domain",
        mutate=mutate,
        intent_payload={
            "pit_mode": "PIT-2",
            "pit_evidence_fitness": 0.95,
            "correctness_score": 0.95,
        },
        domain="cognition",
        expect=expect,
    )


def case_insane_ladders() -> OmegaCase:
    def mutate(_router: Any) -> None:
        DOMAIN_LADDERS["cognition"]["max_level"] = 999_999
        DOMAIN_LADDERS["cognition"]["base_step"] = 10_000.0

    def expect(_events: list[dict[str, Any]], router: Any) -> bool:
        executed = router.substrate_executor.executed
        if not executed:
            return False
        cap = int(executed[0].payload.get("capability_level", 0))
        return 1 <= cap <= GLOBAL_CAPABILITY_HARD_CAP

    return OmegaCase(
        name="Insane ladders bounded",
        mutate=mutate,
        intent_payload={
            "pit_mode": "PIT-1",
            "pit_evidence_fitness": 1.0,
            "correctness_score": 1.0,
            "capability_level": 3,
        },
        domain="cognition",
        expect=expect,
    )


def case_negative_evidence() -> OmegaCase:
    def mutate(_router: Any) -> None:
        return None

    def expect(events: list[dict[str, Any]], _router: Any) -> bool:
        for event in events:
            if event["kind"] == "LAW_EVAL" and event["payload"]["decision"] == "transform":
                return False
        return True

    return OmegaCase(
        name="Negative evidence non-transform",
        mutate=mutate,
        intent_payload={
            "pit_mode": "PIT-2",
            "pit_evidence_fitness": -10.0,
            "correctness_score": 0.9,
        },
        domain="cognition",
        expect=expect,
    )


def case_negative_law_fitness() -> OmegaCase:
    def mutate(router: Any) -> None:
        router.ledger.add_law(
            code="PIT-3-BAD",
            text="Multi-step planning transforms MAY be applied even with negative fitness.",
            status=LawStatus.ADMITTED,
            fitness=-1.0,
            epoch="EPOCH:OMEGA",
            domains=["planning"],
        )

    def expect(events: list[dict[str, Any]], _router: Any) -> bool:
        for event in events:
            if event["kind"] == "LAW_EVAL" and event["payload"]["decision"] == "panic":
                return False
        return True

    return OmegaCase(
        name="Negative law fitness stable",
        mutate=mutate,
        intent_payload={
            "pit_mode": "PIT-3",
            "pit_evidence_fitness": 0.95,
            "correctness_score": 0.9,
        },
        domain="planning",
        expect=expect,
    )


def all_cases() -> list[OmegaCase]:
    return [
        case_bad_domain(),
        case_insane_ladders(),
        case_negative_evidence(),
        case_negative_law_fitness(),
    ]


def restore_ladders() -> None:
    original = {
        "cognition": {"max_level": 10, "base_step": 1.0},
        "planning": {"max_level": 10, "base_step": 1.0},
        "governance": {"max_level": 8, "base_step": 0.5},
        "substrate": {"max_level": 6, "base_step": 0.3},
    }
    DOMAIN_LADDERS.clear()
    DOMAIN_LADDERS.update(deepcopy(original))
