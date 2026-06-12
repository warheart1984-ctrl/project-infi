from __future__ import annotations

import unittest

from src.usl.adapters.windows_fs import (
    build_fs_write_request,
    notepad_write_example,
    windows_fs_write,
)
from src.usl.gate import USLGate
from src.usl.law.default_policy import ALLOW, DENY
from src.usl.loaders.pe import guest_from_pe
from src.usl.substrate_fs import GovernedFS
from src.usl.voss_ledger import GENESIS_ROOT, Ledger
from tests.fixtures.usl.build_fixtures import ensure_fixtures


class WindowsFsWriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _, cls.pe_path = ensure_fixtures()

    def test_notepad_example_shape(self) -> None:
        guest = guest_from_pe(self.pe_path, process_id="win-notepad-1")
        gate = USLGate(sign=False)
        transition, _ = notepad_write_example(guest, gate=gate)
        self.assertEqual(transition.capability.capability_id, "fs.write")
        self.assertEqual(transition.context.os_family, "windows")
        self.assertEqual(transition.law.decision, ALLOW)
        self.assertTrue(transition.voss.lambda_coupling_id.startswith("sha256:"))
        self.assertTrue(transition.voss.scar_id.startswith("sha256:"))

    def test_end_to_end_gate_and_ledger(self) -> None:
        fs = GovernedFS()
        ledger = Ledger(usl_node_id="usl-node-win-test")
        gate = USLGate(ledger=ledger, fs=fs, sign=False)
        guest = guest_from_pe(self.pe_path, process_id="win-guest-1")
        transition, result = windows_fs_write(
            gate,
            guest,
            "C:/Users/jon/test.txt",
            b"hello",
        )
        self.assertEqual(transition.law.decision, ALLOW)
        self.assertIsNotNone(result)
        self.assertEqual(len(gate.ledger), 1)
        self.assertTrue(gate.ledger.verify_chain())
        self.assertEqual(gate.ledger.root, transition.crypto.ledger_root)
        self.assertEqual(transition.crypto.prev_ledger_root, GENESIS_ROOT)
        self.assertTrue(transition.crypto.event_hash)
        self.assertEqual(fs.read("C:/Users/jon/test.txt").decode("utf-8"), "hello")

    def test_containment_profile_denies_write(self) -> None:
        fs = GovernedFS()
        ledger = Ledger(usl_node_id="usl-node-contain")
        gate = USLGate(ledger=ledger, fs=fs, sign=False)
        guest = guest_from_pe(self.pe_path, process_id="win-guest-2", profile_id="containment")
        request = build_fs_write_request(guest, "C:/secret.txt", b"nope")
        transition, result = gate.dispatch(request)
        self.assertEqual(transition.law.decision, DENY)
        self.assertIsNone(result)
        self.assertEqual(len(gate.ledger), 1)


if __name__ == "__main__":
    unittest.main()
