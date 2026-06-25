"""CORI Alpha — runtime governance invariant checks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from nova.bridges import panel_store

from src.continuity.continuity_store import ContinuityStore, get_continuity_store
from src.continuity.law_ledger import LawLedgerStore, default_law_ledger_path


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _payload(row: dict[str, Any]) -> dict[str, Any]:
    return dict(row.get("payload") or {})


@dataclass
class InvariantResult:
    invariant_id: str
    passed: bool
    detail: str
    violations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "invariant_id": self.invariant_id,
            "passed": self.passed,
            "status": "pass" if self.passed else "fail",
            "detail": self.detail,
            "violations": self.violations,
        }


class GovernanceInvariantChecker:
    """Prove the running system never violates core governance invariants."""

    def __init__(
        self,
        *,
        continuity: ContinuityStore | None = None,
        law_store: LawLedgerStore | None = None,
    ) -> None:
        self._continuity = continuity or get_continuity_store()
        self._law_store = law_store or LawLedgerStore(path=default_law_ledger_path())

    def _events(self, event_type: str | None = None, *, limit: int = 5000) -> list[dict[str, Any]]:
        return self._continuity.list_events(event_type=event_type, limit=limit)

    def check_no_execution_without_validation(self) -> InvariantResult:
        """If aaes_exec exists, there must be validation_decided and law_eval."""
        violations: list[str] = []
        law_ids = set()
        for e in self._events("law_eval"):
            body = _payload(e)
            law_ids.add(str(body.get("law_eval_id") or (body.get("payload") or {}).get("id") or ""))
        law_ids.discard("")
        validation_ids = {
            str(_payload(e).get("law_eval_id") or "")
            for e in self._events("validation_decided")
        }
        validation_ids.discard("")
        for event in self._events("aaes_exec"):
            body = _payload(event)
            law_eval_id = str(body.get("law_eval_id") or "")
            exec_id = str(body.get("execution_id") or body.get("trace_id") or event.get("id"))
            if law_eval_id and law_eval_id not in law_ids:
                violations.append(f"aaes_exec {exec_id}: missing law_eval {law_eval_id}")
            if law_eval_id and law_eval_id not in validation_ids:
                violations.append(f"aaes_exec {exec_id}: missing validation_decided for {law_eval_id}")
        passed = not violations
        return InvariantResult(
            invariant_id="no_execution_without_validation",
            passed=passed,
            detail="Every aaes_exec must link to law_eval and validation_decided",
            violations=violations,
        )

    def check_no_validation_without_evidence(self) -> InvariantResult:
        """If validation_decided exists, asset must have evidence_attached."""
        violations: list[str] = []
        evidence_by_asset: dict[str, int] = {}
        for event in self._events("evidence_attached"):
            asset_id = str(_payload(event).get("asset_id") or "")
            if asset_id:
                evidence_by_asset[asset_id] = evidence_by_asset.get(asset_id, 0) + 1

        for event in self._events("validation_decided"):
            body = _payload(event)
            asset_id = str(body.get("asset_id") or "")
            if asset_id and evidence_by_asset.get(asset_id, 0) < 1:
                violations.append(
                    f"validation_decided {event.get('id')}: asset {asset_id} has no evidence_attached"
                )
        passed = not violations
        return InvariantResult(
            invariant_id="no_validation_without_evidence",
            passed=passed,
            detail="Every validation_decided must reference an asset with evidence_attached",
            violations=violations,
        )

    def check_no_governed_mission_without_law_eval(self) -> InvariantResult:
        """If urg_mission governed=True, prior law_eval with matching id must exist."""
        violations: list[str] = []
        law_eval_ids: set[str] = set()
        for e in self._events("law_eval"):
            body = _payload(e)
            law_eval_ids.add(str(body.get("law_eval_id") or (body.get("payload") or {}).get("id") or ""))
        law_eval_ids.discard("")
        for event in self._events("urg_mission"):
            body = _payload(event)
            if not body.get("governed", True):
                continue
            law_eval_id = str(
                body.get("law_eval_id")
                or (body.get("context") or {}).get("law_eval_id")
                or ""
            )
            mission_id = str(body.get("mission_id") or "")
            if law_eval_id and law_eval_id not in law_eval_ids:
                violations.append(f"urg_mission {mission_id}: law_eval_id {law_eval_id} not in continuity")
        passed = not violations
        return InvariantResult(
            invariant_id="no_governed_mission_without_law_eval",
            passed=passed,
            detail="Governed urg_mission events must reference a continuity law_eval",
            violations=violations,
        )

    def check_nova_laws_have_ledger_hash(self) -> InvariantResult:
        """Nova-introduced laws must have a law_ledger row with hash."""
        violations: list[str] = []
        for law in self._law_store.all_laws():
            if law.introduced_by != "nova":
                continue
            if not law.law_hash:
                violations.append(f"law {law.law_id}: missing law_hash")
            has_ledger = any(entry.law_id == law.law_id for entry in self._law_store.ledger_entries())
            if not has_ledger:
                violations.append(f"law {law.law_id}: no law_ledger entry")
        passed = not violations
        return InvariantResult(
            invariant_id="nova_laws_have_ledger_hash",
            passed=passed,
            detail="introduced_by=nova laws must have hash and ledger entry",
            violations=violations,
        )

    def check_panels_match_continuity(self) -> InvariantResult:
        """Each aaes_exec / nexus_event should have a panel referencing execution ids."""
        violations: list[str] = []
        panels = panel_store.get_panel_store().list_panels()
        panel_blob = json.dumps(panels, sort_keys=True, default=str)

        for event_type in ("aaes_exec", "nexus_event"):
            for event in self._events(event_type):
                body = _payload(event)
                needles = [
                    str(body.get("execution_id") or ""),
                    str(body.get("trace_id") or ""),
                    str(body.get("event_id") or ""),
                    str(body.get("mission_id") or ""),
                ]
                needles = [n for n in needles if n]
                if not needles:
                    continue
                if not any(needle in panel_blob for needle in needles):
                    violations.append(
                        f"{event_type} {event.get('id')}: no panel references {needles[0]}"
                    )
        passed = not violations
        return InvariantResult(
            invariant_id="panels_match_continuity",
            passed=passed,
            detail="Execution events must be referenced in panel_store payloads",
            violations=violations,
        )

    def run_all(self) -> list[InvariantResult]:
        return [
            self.check_no_execution_without_validation(),
            self.check_no_validation_without_evidence(),
            self.check_no_governed_mission_without_law_eval(),
            self.check_nova_laws_have_ledger_hash(),
            self.check_panels_match_continuity(),
        ]

    def persist_status(self, results: list[InvariantResult] | None = None) -> None:
        """Update invariant_status table for dashboard traffic lights."""
        rows = results if results is not None else self.run_all()
        with self._continuity._connect() as conn:
            for result in rows:
                conn.execute(
                    """
                    INSERT INTO invariant_status (invariant_id, status, last_run_at, detail_json)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(invariant_id) DO UPDATE SET
                        status = excluded.status,
                        last_run_at = excluded.last_run_at,
                        detail_json = excluded.detail_json
                    """,
                    (
                        result.invariant_id,
                        "pass" if result.passed else "fail",
                        _now(),
                        json.dumps(result.to_dict(), sort_keys=True),
                    ),
                )

    def list_status(self) -> list[dict[str, Any]]:
        with self._continuity._connect() as conn:
            rows = conn.execute(
                "SELECT invariant_id, status, last_run_at, detail_json FROM invariant_status ORDER BY invariant_id"
            ).fetchall()
        return [
            {
                "invariant_id": row["invariant_id"],
                "status": row["status"],
                "last_run_at": row["last_run_at"],
                "detail": json.loads(row["detail_json"] or "{}"),
            }
            for row in rows
        ]


def run_governance_invariants(*, persist: bool = True) -> dict[str, Any]:
    checker = GovernanceInvariantChecker()
    results = checker.run_all()
    if persist:
        checker.persist_status(results)
    return {
        "ran_at": _now(),
        "all_passed": all(r.passed for r in results),
        "results": [r.to_dict() for r in results],
    }
