"""Tests for Jarvis modular memory-board law."""

import unittest

from src.jarvis_memory_board import (
    build_default_memory_controller,
    build_memory_board_snapshot,
    MemoryBoardViolation,
    MemoryController,
    MemoryModule,
    default_memory_slots,
    to_memory_board_envelope,
)


def _module(
    *,
    module_id: str,
    module_class: str,
    supported_slot: str,
    trust_class: str = "verified",
    enabled: bool = True,
) -> MemoryModule:
    return MemoryModule(
        module_id=module_id,
        module_version="1.0.0",
        module_class=module_class,
        supported_slot=supported_slot,
        capacity=256,
        trust_class=trust_class,
        retrieval_priority=80,
        retention_policy="persistent",
        eviction_policy="age_and_rank",
        promotion_rules=("from_session_verified",),
        migration_rules=("to_archive_on_age",),
        enabled=enabled,
    )


class TestJarvisMemoryBoard(unittest.TestCase):
    """Force doctrine violations and prove they are rejected lawfully."""

    def setUp(self):
        self.controller = MemoryController(default_memory_slots())

    def test_default_memory_controller_slots_in_capability_board(self):
        """The canonical board should boot with the linked capability-aware cards installed."""
        controller = build_default_memory_controller()
        snapshot = build_memory_board_snapshot(controller)

        self.assertEqual(snapshot["max_slots"], 10)
        self.assertEqual(snapshot["active_slots"], 6)
        self.assertEqual(snapshot["installed_slots"], 6)
        self.assertEqual(snapshot["reserved_slots"], 4)
        self.assertEqual(snapshot["board"]["board_id"], "capability_adapter_board")
        self.assertIn("aais_capability_module", snapshot["board"]["linked_subsystems"])

        foundation = next(slot for slot in snapshot["slots"] if slot["slot_id"] == "slot_01")
        preference = next(slot for slot in snapshot["slots"] if slot["slot_id"] == "slot_06")
        reserved = next(slot for slot in snapshot["slots"] if slot["slot_id"] == "slot_07")

        self.assertEqual(foundation["module"]["module_id"], "capability_foundation_v2")
        self.assertEqual(preference["module"]["module_id"], "capability_routing_preferences_v2")
        self.assertEqual(foundation["module"]["linked_subsystem"], "aais_capability_module")
        self.assertTrue(reserved["reserved"])
        self.assertFalse(reserved["installed"])

    def test_slot_rejects_direct_install_without_controller_approval(self):
        """A slot may not be populated without controller approval."""
        slot = self.controller.slots["slot_02"]
        module = _module(
            module_id="operational_v1",
            module_class="operational",
            supported_slot="slot_02",
        )

        with self.assertRaises(MemoryBoardViolation) as ctx:
            slot.install(module)

        self.assertIn("controller approval", str(ctx.exception))
        self.assertIsNone(slot.module)

    def test_replacement_cannot_change_slot_purpose(self):
        """A better module may upgrade a slot, but it may not change what the slot is for."""
        original = _module(
            module_id="operational_v1",
            module_class="operational",
            supported_slot="slot_02",
        )
        self.controller.register_module("slot_02", original)

        violating_replacement = _module(
            module_id="foundation_v9",
            module_class="foundation",
            supported_slot="slot_02",
        )

        with self.assertRaises(MemoryBoardViolation) as ctx:
            self.controller.swap_module("slot_02", violating_replacement, migration_records=[])

        self.assertIn("purpose", str(ctx.exception))
        self.assertEqual(self.controller.slots["slot_02"].module.module_id, "operational_v1")

    def test_migration_rejects_trust_or_role_violation(self):
        """Old memory may move only if trust class and slot role are preserved."""
        original = _module(
            module_id="operational_v1",
            module_class="operational",
            supported_slot="slot_02",
            trust_class="verified",
        )
        self.controller.register_module("slot_02", original)

        replacement = _module(
            module_id="operational_v2",
            module_class="operational",
            supported_slot="slot_02",
            trust_class="verified",
        )

        violating_record = {
            "record_id": "memory-1",
            "slot_id": "slot_02",
            "slot_role": "session",
            "trust_class": "verified",
            "text": "Temporary thread context should not land as operational truth.",
        }

        with self.assertRaises(MemoryBoardViolation) as ctx:
            self.controller.swap_module(
                "slot_02",
                replacement,
                migration_records=[violating_record],
            )

        self.assertIn("slot role=operational", str(ctx.exception))
        self.assertEqual(self.controller.slots["slot_02"].module.module_id, "operational_v1")
        self.assertEqual(self.controller.migration_log, [])

    def test_lawful_swap_preserves_role_and_trust(self):
        """A compatible replacement can activate when migration stays lawful."""
        original = _module(
            module_id="operational_v1",
            module_class="operational",
            supported_slot="slot_02",
            trust_class="verified",
        )
        self.controller.register_module("slot_02", original)

        replacement = _module(
            module_id="operational_v2",
            module_class="operational",
            supported_slot="slot_02",
            trust_class="verified",
        )

        result = self.controller.swap_module(
            "slot_02",
            replacement,
            migration_records=[
                {
                    "record_id": "memory-1",
                    "slot_id": "slot_02",
                    "slot_role": "operational",
                    "trust_class": "verified",
                    "text": "Verified recurring architecture truth.",
                },
                {
                    "record_id": "memory-1",
                    "slot_id": "slot_02",
                    "slot_role": "operational",
                    "trust_class": "verified",
                    "text": "Verified recurring architecture truth.",
                },
            ],
        )

        self.assertEqual(result["activated_module"].module_id, "operational_v2")
        self.assertEqual(len(result["migrated_records"]), 1)
        self.assertEqual(self.controller.slots["slot_02"].module.module_id, "operational_v2")
        self.assertEqual(self.controller.slots["slot_02"].retired_modules[0].module_id, "operational_v1")
        self.assertFalse(self.controller.slots["slot_02"].retired_modules[0].enabled)
        self.assertEqual(self.controller.migration_log[0]["migrated_record_count"], 1)

    def test_memory_board_envelope_matches_schema_shape(self):
        """Board snapshots should map to jarvis_memory_board.v1."""
        controller = build_default_memory_controller()
        envelope = to_memory_board_envelope(build_memory_board_snapshot(controller))
        self.assertEqual(envelope["jarvis_memory_board_version"], "jarvis_memory_board.v1")
        self.assertGreaterEqual(len(envelope["slots"]), 1)
        self.assertTrue(envelope["controller_state"]["approval_required"])


if __name__ == "__main__":
    unittest.main()
