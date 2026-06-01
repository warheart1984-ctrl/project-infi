"""Focused tests for the narrowed Project Infi runtime loop."""

from datetime import datetime, timedelta
from src.datetime_compat import UTC
import unittest
from unittest.mock import patch

from src.project_infi_state_machine import (
    CHRONOS_TTL_EVENT,
    CycleContext,
    CycleDisposition,
    ExecutionResult,
    FRACTURE_REVIEW_EVENT,
    GAMMA_LEGITIMACY_EVENT,
    ProjectInfiStateMachine,
    ProposedChange,
    RECOVERY_DRIFT_EVENT,
    WAIT_RECHECK_EVENT,
)


class TestProjectInfiStateMachine(unittest.TestCase):
    """Verify the four locked runtime behaviors."""

    def setUp(self):
        self.machine = ProjectInfiStateMachine()

    @staticmethod
    def _utc_time(hour: int = 12, minute: int = 0, second: int = 0) -> datetime:
        return datetime(2026, 4, 15, hour, minute, second, tzinfo=UTC)

    @staticmethod
    def _lawful_context() -> CycleContext:
        return CycleContext(bound_flag=True)

    @staticmethod
    def _truthful_request(**overrides) -> ProposedChange:
        payload = {
            "kind": "repo_change",
            "authority": "forge",
            "context_valid": True,
            "protected_access_requested": False,
            "operator_approved": True,
            "risk_level": "medium",
            "evidence_present": True,
            "design_quality": 0.92,
            "debt_pressure": 0,
            "external_influence": "forge_lane",
        }
        payload.update(overrides)
        return ProposedChange(**payload)

    def test_truth_guard_returns_rejected_no_admission_without_calling_admit(self):
        ctx = self._lawful_context()
        request = self._truthful_request(design_quality=0.2)

        with patch.object(self.machine, "admit", wraps=self.machine.admit) as mock_admit:
            result = self.machine.run_cycle(ctx, request, now=self._utc_time())

        self.assertEqual(result["status"], CycleDisposition.REJECTED_NO_ADMISSION.value)
        self.assertFalse(result["final_truth"].truthful)
        mock_admit.assert_not_called()
        self.assertNotIn("admit", {entry["event"] for entry in result["event_log"]})

    def test_chronos_ttl_always_produces_a_ready_time(self):
        ctx = self._lawful_context()
        request = self._truthful_request(kind="overload", submitted_at=self._utc_time())

        l1 = self.machine.verify_l1(ctx, request)
        j1010 = self.machine.judge_1010(ctx, request, l1)
        debt = self.machine.reckon_1111(ctx, request, l1, j1010)
        final_truth = self.machine.verify_l2(ctx, l1, j1010, debt)
        legitimacy = self.machine.legitimacy_gate(ctx, request, self.machine.assess_burden(debt.record, ctx.risk_profile))
        ttl, scores = self.machine.compute_adaptive_ttl(ctx, request, l1, j1010, debt, final_truth, legitimacy)
        ready_at = request.submitted_at + ttl

        self.assertIsInstance(ttl, timedelta)
        self.assertGreaterEqual(ttl.total_seconds(), 0)
        self.assertIsInstance(ready_at, datetime)
        self.assertEqual(ready_at.tzinfo, UTC)
        self.assertIn("ttl_seconds", scores)
        self.assertEqual(scores["ttl_seconds"], int(ttl.total_seconds()))

    def test_wait_path_always_moves_state_and_schedules_recheck(self):
        ctx = self._lawful_context()
        now = self._utc_time()
        request = self._truthful_request(kind="overload", submitted_at=now)

        result = self.machine.run_cycle(ctx, request, now=now)

        self.assertEqual(result["status"], CycleDisposition.WAIT.value)
        self.assertGreater(result["ttl_seconds"], 0)
        self.assertIsNotNone(request.next_check_at)
        self.assertGreater(request.next_check_at, now)
        self.assertEqual(request.recheck_count, 1)
        self.assertEqual(ctx.wait_count, 1)
        self.assertTrue(any(entry["event"] == CHRONOS_TTL_EVENT for entry in result["event_log"]))
        self.assertTrue(any(entry["event"] == RECOVERY_DRIFT_EVENT for entry in result["event_log"]))
        self.assertTrue(any(entry["event"] == WAIT_RECHECK_EVENT for entry in result["event_log"]))

    def test_wait_path_re_evaluates_and_eventually_admits(self):
        ctx = self._lawful_context()
        submitted_at = self._utc_time()
        request = self._truthful_request(kind="overload", submitted_at=submitted_at)

        first = self.machine.run_cycle(ctx, request, now=submitted_at)
        self.assertEqual(first["status"], CycleDisposition.WAIT.value)

        later = submitted_at + timedelta(minutes=20)
        second = self.machine.run_cycle(ctx, request, now=later)

        self.assertNotEqual(second["status"], CycleDisposition.WAIT.value)
        self.assertTrue(second["final_truth"].truthful)
        self.assertIn("admitted", second)
        self.assertEqual(second["next_state"], "1000")

    def test_fracture_is_recoverable_and_operator_aware_not_terminal(self):
        ctx = self._lawful_context()
        ctx.risk_profile = self.machine.FRACTURE_THRESHOLD
        now = self._utc_time()
        request = self._truthful_request(submitted_at=now)

        first = self.machine.run_cycle(ctx, request, now=now)

        self.assertEqual(first["status"], CycleDisposition.WAIT.value)
        self.assertTrue(ctx.operator_review_required)
        self.assertTrue(any(entry["event"] == FRACTURE_REVIEW_EVENT for entry in first["event_log"]))
        self.assertLess(ctx.risk_profile, self.machine.FRACTURE_THRESHOLD + 1)

        second = self.machine.run_cycle(ctx, request, now=now + timedelta(minutes=20))
        self.assertNotEqual(second["status"], CycleDisposition.REJECTED_NO_ADMISSION.value)
        self.assertNotEqual(second["status"], "rejected")
        self.assertTrue(second["final_truth"].truthful)

    def test_ready_cycle_admits_normally_when_now_reaches_ready_at(self):
        ctx = self._lawful_context()
        now = self._utc_time()
        request = self._truthful_request(submitted_at=now - timedelta(minutes=1))

        result = self.machine.run_cycle(ctx, request, now=now)

        self.assertTrue(result["final_truth"].truthful)
        self.assertIn("admitted", result)
        self.assertIn(GAMMA_LEGITIMACY_EVENT, {entry["event"] for entry in result["event_log"]})
        self.assertEqual(result["next_state"], "1000")
        self.assertEqual(result["admitted"].prime_depth, 4)


if __name__ == "__main__":
    unittest.main()
