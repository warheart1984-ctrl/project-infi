"""Constitutional bootloader — fail-closed gate before any governed runtime starts.

This module is the authoritative constitutional guardrail. Tool-level checks live in
``operator_kernel.governance_gate`` (path/command allowlists). This gate verifies:

- transition ledger integrity
- immutable core (Articles XIII–XVI, SEVEN_INVARIANTS)
- no unobserved amendments
- observer replay for all constitutional StateObjects
- closed states have transition receipts

Set ``CONSTITUTIONAL_BOOT_SKIP=1`` only for isolated tests or emergency recovery.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from constitutional.core.graph import validate_transition
from constitutional.core.observer import ObserverVerificationEngine
from constitutional.runtime.receipts_v2 import (
    IMMUTABLE_CORE_ARTICLES,
    AmendmentReceiptV2,
    is_receipt_v2_complete,
    validate_immutable_amendment,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime

if TYPE_CHECKING:
    pass

IMMUTABLE_ARTICLES = frozenset({"XIII", "XIV", "XV", "XVI"})
IMMUTABLE_INVARIANTS = frozenset({"SEVEN_INVARIANTS"})
AMENDMENT_STATE_TYPES = frozenset({"amendment", "AmendmentState", "constitutional_amendment"})
AMENDMENT_OBSERVED_CONSTITUTIONAL = frozenset({"Observed", "Closed"})
AMENDMENT_OBSERVED_STAGE = frozenset({"observed", "closed"})
TERMINAL_CONSTITUTIONAL = frozenset({"Closed"})

_BOOT_COMPLETED = False


class GovernanceGateFailed(RuntimeError):
    """Raised when the constitutional bootloader refuses to start."""

    def __init__(self, check: str, message: str, *, failures: list[str] | None = None) -> None:
        self.check = check
        self.failures = failures or [message]
        detail = "; ".join(self.failures)
        super().__init__(f"[{check}] {detail}")


@dataclass
class BootCheckReport:
    ok: bool
    runtime: str
    failures: list[str] = field(default_factory=list)


@dataclass
class GovernanceBootReport:
    ok: bool
    checks: list[BootCheckReport] = field(default_factory=list)

    @property
    def failures(self) -> list[str]:
        out: list[str] = []
        for check in self.checks:
            for failure in check.failures:
                out.append(f"{check.runtime}:{failure}")
        return out


def boot_skipped() -> bool:
    return os.getenv("CONSTITUTIONAL_BOOT_SKIP", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def collect_runtime_csrs() -> list[tuple[str, ConstitutionalStateRuntime]]:
    """Discover process-wide CSRs (operator, URG, AAIS)."""
    runtimes: list[tuple[str, ConstitutionalStateRuntime]] = []
    try:
        from operator_kernel.csr import CSR as operator_csr

        runtimes.append(("operator", operator_csr))
    except Exception:
        pass
    try:
        from src.ugr.state_runtime import CSR as urg_csr

        runtimes.append(("urg", urg_csr))
    except Exception:
        pass
    try:
        from src.aaes_os.csr_bridge import get_aais_csr

        runtimes.append(("aais", get_aais_csr()))
    except Exception:
        pass
    return runtimes


def hydrate_csr_from_disk(csr: ConstitutionalStateRuntime) -> int:
    """Load all persisted constitutional state under a CSR persist root."""
    root = csr._persist_root  # noqa: SLF001 — boot hydration
    if root is None or not root.is_dir():
        return 0
    loaded = 0
    for child in root.iterdir():
        if child.is_dir() and (child / "constitutional_state.json").is_file():
            csr.load_task_persisted(child.name, child)
            loaded += 1
    return loaded


def all_constitutional_state_ids(csr: ConstitutionalStateRuntime) -> list[str]:
    return list(csr._states.keys())  # noqa: SLF001


def constitutional_states_of_type(
    csr: ConstitutionalStateRuntime,
    state_type: str,
) -> list:
    with csr._lock:  # noqa: SLF001
        return [
            state.model_copy(deep=True)
            for state in csr._states.values()
            if state.state_type == state_type
        ]


def _load_amendment_receipts_from_disk() -> list[AmendmentReceiptV2]:
    path = Path(".runtime/receipts/all_receipts.jsonl")
    if not path.is_file():
        return []
    receipts: list[AmendmentReceiptV2] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("action_type") != "constitutional_amendment":
                continue
            try:
                receipts.append(AmendmentReceiptV2.model_validate(payload))
            except Exception:
                continue
    return receipts


def _article_key(article: str) -> str:
    return article.upper().replace("ARTICLE ", "").strip()


def check_ledger_integrity(csr: ConstitutionalStateRuntime) -> list[str]:
    failures: list[str] = []
    ledger = csr.ledger
    for detected in ledger.detect_failures():
        failures.append(f"{detected.code}: {detected.message}")

    for entry in ledger.entries:
        try:
            validate_transition(entry.from_state, entry.to_state)
        except ValueError as exc:
            failures.append(f"illegal transition {entry.from_state}→{entry.to_state}: {exc}")
        if not entry.legal_basis:
            failures.append(f"missing legal_basis on ledger entry {entry.receipt_id}")
        if not entry.accountable_party:
            failures.append(f"missing accountable_party on ledger entry {entry.receipt_id}")
    return failures


def check_immutable_core(
    csr: ConstitutionalStateRuntime,
    *,
    amendment_receipts: list[AmendmentReceiptV2] | None = None,
) -> list[str]:
    failures: list[str] = []
    receipts = amendment_receipts if amendment_receipts is not None else _load_amendment_receipts_from_disk()

    for receipt in receipts:
        if not is_receipt_v2_complete(receipt):
            failures.append(f"incomplete amendment receipt {receipt.receipt_id}")
            continue
        try:
            validate_immutable_amendment(receipt.amendment)
        except ValueError as exc:
            failures.append(str(exc))

    for state in constitutional_states_of_type(csr, "AmendmentState"):
        article_tag = next((tag for tag in state.invariants if tag.startswith("article:")), None)
        if not article_tag:
            continue
        article = _article_key(article_tag.split(":", 1)[1])
        if article not in IMMUTABLE_CORE_ARTICLES:
            continue
        if "immutable_override" not in state.evidence_requirements:
            failures.append(f"illegal amendment to immutable article {article} on {state.state_id}")

    return failures


def check_unobserved_amendments(csr: ConstitutionalStateRuntime) -> list[str]:
    failures: list[str] = []
    for state_type in AMENDMENT_STATE_TYPES:
        for state in constitutional_states_of_type(csr, state_type):
            if state.current_state not in AMENDMENT_OBSERVED_CONSTITUTIONAL:
                failures.append(
                    f"unobserved amendment StateObject {state.state_id} "
                    f"(current_state={state.current_state})"
                )

    for receipt in _load_amendment_receipts_from_disk():
        if receipt.amendment.amendment_stage not in AMENDMENT_OBSERVED_STAGE:
            failures.append(
                f"unobserved amendment receipt {receipt.receipt_id} "
                f"(stage={receipt.amendment.amendment_stage})"
            )

    return failures


def check_closed_states_have_receipts(csr: ConstitutionalStateRuntime) -> list[str]:
    failures: list[str] = []
    for state_id in all_constitutional_state_ids(csr):
        state = csr.get_state(state_id)
        if state.current_state not in TERMINAL_CONSTITUTIONAL:
            continue
        if not csr.receipts_for(state_id):
            failures.append(f"missing transition receipts for closed state {state_id}")
    return failures


def check_replay_for_all(csr: ConstitutionalStateRuntime) -> list[str]:
    """Observer replay for every constitutional object (core CSR replay path)."""
    failures: list[str] = []
    observer = ObserverVerificationEngine(csr)
    for state_id in all_constitutional_state_ids(csr):
        try:
            result = observer.verify_state(state_id)
        except KeyError:
            failures.append(f"unknown state during verification: {state_id}")
            continue
        if result.divergence_detected:
            failures.append(f"divergence detected in {state_id}")
    return failures


def run_boot_checks_for_csr(
    runtime_name: str,
    csr: ConstitutionalStateRuntime,
    *,
    hydrate: bool = True,
) -> BootCheckReport:
    if hydrate:
        hydrate_csr_from_disk(csr)

    failures: list[str] = []
    failures.extend(check_ledger_integrity(csr))
    failures.extend(check_immutable_core(csr))
    failures.extend(check_unobserved_amendments(csr))
    failures.extend(check_replay_for_all(csr))
    failures.extend(check_closed_states_have_receipts(csr))
    return BootCheckReport(ok=not failures, runtime=runtime_name, failures=failures)


def governance_gate(
    *,
    csrs: list[tuple[str, ConstitutionalStateRuntime]] | None = None,
    hydrate: bool = True,
) -> GovernanceBootReport:
    """Run all constitutional boot checks. Returns aggregate report (does not raise)."""
    if boot_skipped():
        return GovernanceBootReport(ok=True, checks=[BootCheckReport(ok=True, runtime="skipped")])

    targets = csrs if csrs is not None else collect_runtime_csrs()
    if not targets:
        targets = [("local", ConstitutionalStateRuntime())]

    checks = [run_boot_checks_for_csr(name, csr, hydrate=hydrate) for name, csr in targets]
    return GovernanceBootReport(ok=all(c.ok for c in checks), checks=checks)


def assert_constitutional_boot(
    *,
    csrs: list[tuple[str, ConstitutionalStateRuntime]] | None = None,
    hydrate: bool = True,
) -> GovernanceBootReport:
    """Fail-closed boot — raises GovernanceGateFailed or exits when checks fail."""
    report = governance_gate(csrs=csrs, hydrate=hydrate)
    if report.ok:
        return report

    failures = report.failures
    raise GovernanceGateFailed("governance_gate", failures[0] if failures else "boot failed", failures=failures)


def require_constitutional_boot() -> None:
    """Called at Operator / AAIS / URG / Nova startup. Exits process on failure."""
    global _BOOT_COMPLETED
    if boot_skipped():
        return
    if _BOOT_COMPLETED:
        return
    try:
        assert_constitutional_boot()
    except GovernanceGateFailed as exc:
        raise SystemExit(f"Governance gate failed — refusing to run: {exc}") from exc
    refresh_global_constitutional_snapshots()
    try:
        from constitutional.runtime.risk_runtime import refresh_constitutional_risk_forecasts

        refresh_constitutional_risk_forecasts()
    except ImportError:
        pass
    _BOOT_COMPLETED = True


def refresh_global_constitutional_snapshots() -> None:
    """Aggregate governed global constitutional state for each runtime CSR."""
    try:
        from constitutional.runtime.constitutional_state_model import (
            ConstitutionalStateModel,
        )
    except ImportError:
        return
    for _name, csr in collect_runtime_csrs():
        try:
            ConstitutionalStateModel(csr).update_snapshot()
        except Exception:
            continue
