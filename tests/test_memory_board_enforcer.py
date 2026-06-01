"""Tests for the strict live memory gateway."""

from pathlib import Path
import shutil
import tempfile
import unittest

from src.governance_layer import GovernanceLayer
from src.immune_system import ImmuneSystemController
from src.jarvis_operator import JarvisMemoryStore
from src.memory_board_enforcer import (
    MemoryBoardBypassError,
    MemoryBoardEnforcer,
    MemoryBoardEnforcerError,
)
from src.module_governance import ModuleGovernanceController
from src.phase_gate import Phase, demote_component, reset_registry
from src.seam_log import list_seam_events


class TestMemoryBoardEnforcer(unittest.TestCase):
    """Verify that live memory mutations must cross the gateway."""

    def setUp(self):
        reset_registry()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="memory-board-enforcer-"))
        self.store = JarvisMemoryStore(memory_path=self.temp_dir / "jarvis_memory.json")
        self.immune = ImmuneSystemController(runtime_dir=self.temp_dir / "immune")
        self.governance = GovernanceLayer(runtime_dir=self.temp_dir / "governance")
        self.module_governance = ModuleGovernanceController(
            runtime_dir=self.temp_dir / "module-governance",
            immune_controller=self.immune,
            governance_controller=self.governance,
        )
        self.immune.reset()
        self.governance.reset()
        self.module_governance.reset()
        self.enforcer = MemoryBoardEnforcer(
            self.store,
            immune_controller=self.immune,
            module_governance_controller=self.module_governance,
        )

    def tearDown(self):
        reset_registry()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_enforcer_routes_memory_write_through_board(self):
        """A live write should pass through phase/module gates and land in the board-governed store."""
        memory = self.enforcer.add_memory(
            "Keep Jarvis local-first for operator memory work.",
            category="preference",
            runtime_context="live_runtime",
        )

        self.assertEqual(memory["content"], "Keep Jarvis local-first for operator memory work.")
        self.assertEqual(self.store.last_board_event()["action"], "write")
        audit = self.enforcer.last_audit()
        self.assertEqual(audit["decision"], "ALLOW")
        self.assertEqual(audit["phase_gate"]["decision"], "ALLOW")
        self.assertEqual(audit["module_governance"]["decision"], "ALLOW")
        module = self.module_governance.get_module(self.enforcer.component_id)
        self.assertEqual(module["status"], "admitted")

    def test_dreamspace_runtime_reads_are_admitted_through_the_gateway(self):
        """Dreamspace reads should keep their own admitted runtime label instead of borrowing operator access."""
        self.enforcer.add_memory(
            "Keep Dreamspace reflective but governed.",
            category="preference",
            runtime_context="operator_runtime",
        )

        memories = self.enforcer.list_memories(
            runtime_context="dreamspace_runtime",
        )

        self.assertEqual(len(memories), 1)
        audit = self.enforcer.last_audit()
        self.assertEqual(audit["decision"], "ALLOW")
        self.assertEqual(audit["runtime_context"], "dreamspace_runtime")
        self.assertEqual(audit["phase_gate"]["runtime_context"], "dreamspace_runtime")

    def test_direct_store_mutation_is_blocked_after_enforcer_attaches(self):
        """Direct store writes should fail closed once the live gateway is active."""
        with self.assertRaises(MemoryBoardBypassError):
            self.store.add_memory("Bypass the gateway and write directly.")

        audit = self.enforcer.last_audit()
        self.assertTrue(audit["bypass_detected"])
        self.assertEqual(audit["decision"], "BLOCK")
        module = self.module_governance.get_module(self.enforcer.component_id)
        self.assertEqual(module["status"], "quarantined")
        immune_snapshot = self.immune.snapshot(limit_events=6, limit_incidents=6)
        self.assertGreaterEqual(immune_snapshot["event_count"], 1)

    def test_direct_store_read_is_blocked_after_enforcer_attaches(self):
        """Direct store reads should fail closed once the live gateway is active."""
        with self.assertRaises(MemoryBoardBypassError):
            self.store.list_memories()

        audit = self.enforcer.last_audit()
        self.assertTrue(audit["bypass_detected"])
        self.assertEqual(audit["decision"], "BLOCK")
        self.assertEqual(audit["operation"], "list_memories")

    def test_memory_helper_reads_require_gateway_authority(self):
        """Public store helper reads should fail closed while the enforcer path stays usable."""
        self.enforcer.add_memory(
            "Keep governance snapshots routed through the memory board gateway.",
            category="preference",
            runtime_context="operator_runtime",
        )
        governed_snapshot = self.enforcer.build_governance_snapshot(runtime_context="operator_runtime")
        self.assertIn("counts", governed_snapshot)
        self.assertEqual(governed_snapshot["counts"]["why_gaps"], 1)
        self.assertIsInstance(
            self.enforcer.detect_conflicts(runtime_context="operator_runtime"),
            list,
        )

        raw_helper_calls = [
            ("build_summary", lambda: self.store.build_summary()),
            ("list_archived_memories", lambda: self.store.list_archived_memories()),
            ("list_why_gaps", lambda: self.store.list_why_gaps()),
            ("suggest_merge_candidates", lambda: self.store.suggest_merge_candidates()),
            ("detect_conflicts", lambda: self.store.detect_conflicts()),
            ("build_governance_snapshot", lambda: self.store.build_governance_snapshot()),
        ]

        for operation_name, operation in raw_helper_calls:
            with self.subTest(operation=operation_name):
                with self.assertRaises(MemoryBoardBypassError):
                    operation()

    def test_phase_gate_blocks_live_runtime_when_component_demoted(self):
        """Live writes should stop when the gateway is no longer admitted for live runtime."""
        demote_component(
            self.enforcer.component_id,
            Phase.VALIDATED,
            reason="Phase gate containment for test.",
        )

        with self.assertRaises(MemoryBoardEnforcerError):
            self.enforcer.add_memory(
                "This write should be phase-gated.",
                runtime_context="live_runtime",
            )

        audit = self.enforcer.last_audit()
        self.assertEqual(audit["decision"], "BLOCK")
        self.assertEqual(audit["phase_gate"]["decision"], "BLOCK")
        self.assertEqual(audit["phase_gate"]["component"]["phase"], "validated")

    def test_module_governance_blocks_mutation_when_gateway_is_quarantined(self):
        """Mutations should stop when module governance quarantines the gateway."""
        self.module_governance.report_runtime_signal(
            self.enforcer.component_id,
            signal_type="unauthorized_memory_creation",
            reason="Simulated bypass containment.",
        )

        with self.assertRaises(MemoryBoardEnforcerError):
            self.enforcer.add_memory(
                "This write should be blocked after quarantine.",
                runtime_context="operator_runtime",
            )

        audit = self.enforcer.last_audit()
        self.assertEqual(audit["decision"], "BLOCK")
        self.assertEqual(audit["module_governance"]["decision"], "BLOCK")
        self.assertEqual(audit["module_governance"]["status"], "quarantined")

    def test_module_governance_blocks_reads_when_gateway_is_quarantined(self):
        """Reads should also fail closed once the gateway is quarantined."""
        self.module_governance.report_runtime_signal(
            self.enforcer.component_id,
            signal_type="unauthorized_memory_creation",
            reason="Simulated bypass containment.",
        )

        with self.assertRaises(MemoryBoardEnforcerError):
            self.enforcer.list_memories(runtime_context="operator_runtime")

        audit = self.enforcer.last_audit()
        self.assertEqual(audit["decision"], "BLOCK")
        self.assertEqual(audit["module_governance"]["decision"], "BLOCK")
        self.assertEqual(audit["module_governance"]["status"], "quarantined")
        seam_events = list_seam_events(runtime_dir=self.module_governance.runtime_dir, limit=20)
        self.assertTrue(any(item["event_type"] == "memory_operation_blocked" for item in seam_events))
        self.assertTrue(any(item["classification"] == "boundary_violation" for item in seam_events))


if __name__ == "__main__":
    unittest.main()
