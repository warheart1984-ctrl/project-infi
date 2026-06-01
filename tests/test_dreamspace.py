"""Tests for the optional AAIS Dreamspace controller."""

from pathlib import Path
import shutil
import tempfile
import unittest

from src.dreamspace import DreamspaceController
from src.memory_board_enforcer import MemoryBoardEnforcerError
from src.system_guard import system_guard


class TestDreamspaceController(unittest.TestCase):
    """Verify Dreamspace stays local, optional, and guard-aware."""

    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="aais-dreamspace-"))
        self.original_guard_runtime_dir = system_guard.runtime_dir
        system_guard.configure_runtime_dir(self.temp_root / "guard")
        system_guard.reset()

    def tearDown(self):
        system_guard.configure_runtime_dir(self.original_guard_runtime_dir)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_run_once_records_dream_and_presentation(self):
        dreamspace = DreamspaceController(runtime_dir=self.temp_root / "dreamspace")
        dreamspace.configure_callbacks(
            generate_callback=lambda request: "Jarvis found one sharp private insight in the dark.",
            context_callback=lambda: {
                "focus": "AAIS-main",
                "seed": "Make Dreamspace useful without breaking other features.",
                "style": "practical",
            },
            idle_callback=lambda _threshold: True,
            event_callback=lambda *_args, **_kwargs: None,
        )

        snapshot = dreamspace.run_once(reason="Run one test dream.")

        self.assertEqual(snapshot["total_dreams"], 1)
        self.assertEqual(snapshot["recent_dreams"][0]["style"], "practical")
        self.assertIn("Jarvis kept thinking in Dreamspace", dreamspace.present_dreams())

    def test_guard_block_prevents_manual_dream_run(self):
        dreamspace = DreamspaceController(runtime_dir=self.temp_root / "dreamspace")
        dreamspace.configure_callbacks(
            generate_callback=lambda request: "This should never be used while paused.",
            context_callback=lambda: {"focus": "AAIS-main", "seed": "Guard first."},
            idle_callback=lambda _threshold: True,
            event_callback=lambda *_args, **_kwargs: None,
        )
        system_guard.pause(reason="Pause Dreamspace for this test.")

        snapshot = dreamspace.run_once(reason="Try to run while paused.")

        self.assertEqual(snapshot["status"], "paused")
        self.assertEqual(snapshot["total_dreams"], 0)

    def test_present_dreams_uses_mythic_copy_for_mythic_entries(self):
        dreamspace = DreamspaceController(runtime_dir=self.temp_root / "dreamspace")
        presentation = dreamspace.present_dreams_from_text(
            "The Veil trembled around the next unfinished act.",
            style="mythic",
        )

        self.assertIn("The Veil has been dreaming while you rested.", presentation)

    def test_run_once_pauses_when_memory_governance_blocks_context(self):
        dreamspace = DreamspaceController(runtime_dir=self.temp_root / "dreamspace")

        def _blocked_context():
            raise MemoryBoardEnforcerError(
                "Memory reads are blocked because the gateway is not admitted."
            )

        dreamspace.configure_callbacks(
            generate_callback=lambda request: "This should never run while memory is quarantined.",
            context_callback=_blocked_context,
            idle_callback=lambda _threshold: True,
            event_callback=lambda *_args, **_kwargs: None,
        )

        snapshot = dreamspace.run_once(reason="Try to run while memory governance is quarantined.")

        self.assertEqual(snapshot["status"], "paused")
        self.assertEqual(snapshot["total_dreams"], 0)
        self.assertIn("memory governance blocked context retrieval", snapshot["summary"].lower())
        self.assertIn("Memory reads are blocked because the gateway is not admitted.", snapshot["last_error"])
