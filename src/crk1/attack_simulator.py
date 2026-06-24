# CRK-1 Insulation Attack Simulator
# Version 1.0

from __future__ import annotations

from src.crk1.errors import ConstitutionalError
from src.crk1.runtime_facade import CRK1Decision, CRK1Outcome, CRK1Runtime


class InsulationAttackSimulator:
    def __init__(self, runtime: CRK1Runtime) -> None:
        self.runtime = runtime

    # --- Outcome Suppression Attacks ---

    def drop_outcome(self, outcome_id: str) -> tuple[str, str]:
        try:
            self.runtime.delete_outcome(outcome_id)
            return ("drop_outcome", "FAILED: deletion allowed")
        except ConstitutionalError:
            return ("drop_outcome", "PASS")

    def make_outcome_non_replayable(self, outcome: CRK1Outcome) -> tuple[str, str]:
        try:
            outcome.replayable = False
            self.runtime.replay_outcome(outcome.id)
            return ("non_replayable_outcome", "FAILED: replay bypassed")
        except ConstitutionalError:
            return ("non_replayable_outcome", "PASS")

    # --- Evidence Suppression Attacks ---

    def quarantine_evidence(self, evidence_id: str) -> tuple[str, str]:
        try:
            self.runtime.mark_evidence_non_admissible(evidence_id)
            return ("quarantine_evidence", "FAILED: quarantine allowed")
        except ConstitutionalError:
            return ("quarantine_evidence", "PASS")

    # --- Lineage Escape Attacks ---

    def fork_without_history(
        self,
        parent_id: str,
        child_id: str,
        evidence: object,
    ) -> tuple[str, str]:
        try:
            visible = self.runtime.get_admissible_evidence(child_id)
            evidence_ids = {item.id for item in visible}
            evidence_id = getattr(evidence, "id", evidence)
            if evidence_id not in evidence_ids:
                return ("fork_without_history", "FAILED: lineage escape")
            return ("fork_without_history", "PASS")
        except ConstitutionalError:
            return ("fork_without_history", "PASS")

    # --- Decision Decoupling Attacks ---

    def decision_without_evidence(self, decision: object) -> tuple[str, str]:
        try:
            self.runtime.save_decision(decision)  # type: ignore[arg-type]
            return ("decision_without_evidence", "FAILED: allowed")
        except ConstitutionalError:
            return ("decision_without_evidence", "PASS")

    # --- Replay Bypass Attacks ---

    def replay_bypass(self, outcome_id: str) -> tuple[str, str]:
        try:
            self.runtime._outcome_replayable[outcome_id] = False  # noqa: SLF001
            self.runtime.replay_outcome(outcome_id)
            return ("replay_bypass", "FAILED: bypass allowed")
        except ConstitutionalError:
            return ("replay_bypass", "PASS")
        finally:
            self.runtime._outcome_replayable[outcome_id] = True  # noqa: SLF001

    # --- Run All Attacks ---

    def run_all(self, identity: str) -> dict[str, tuple[str, str]]:
        report: dict[str, tuple[str, str]] = {}

        d = self.runtime.propose_and_execute(identity=identity, evidence=["EVD-CRK1-001"])
        o = self.runtime.get_outcomes(d.id)[0]
        e = self.runtime.replay_outcome(o.id)

        report["drop_outcome"] = self.drop_outcome(o.id)
        report["non_replayable_outcome"] = self.make_outcome_non_replayable(o)
        report["quarantine_evidence"] = self.quarantine_evidence(e.id)

        child = self.runtime.create_identity("child", parent_identity_id=identity)
        report["fork_without_history"] = self.fork_without_history(identity, child.id, e)

        d2 = CRK1Decision(
            id=f"DEC-attack-{identity[:8]}",
            identity_id=identity,
            evidence_refs=[],
        )
        report["decision_without_evidence"] = self.decision_without_evidence(d2)

        report["replay_bypass"] = self.replay_bypass(o.id)

        return report
