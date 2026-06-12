from __future__ import annotations

import unittest
from pathlib import Path

from src.usl.gate import USLGate
from src.usl.loaders.pe import GuestProcess, guest_from_pe, load_pe
from src.usl.substrate_fs import GovernedFS
from src.usl.voss_ledger import Ledger
from tests.fixtures.usl.build_fixtures import ensure_fixtures


class PeLoaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _, cls.pe_path = ensure_fixtures()

    def test_load_minimal_pe_produces_ubo(self) -> None:
        ubo, _address_space = load_pe(self.pe_path)
        self.assertEqual(ubo.os_family, "windows")
        self.assertEqual(ubo.architecture, "x86_64")
        self.assertTrue(ubo.binary_id.startswith("sha256:"))
        self.assertGreater(ubo.entry_point, 0)
        self.assertGreater(len(ubo.imports), 0)
        names = {imp.symbol for imp in ubo.imports}
        self.assertIn("CreateFileW", names)
        self.assertIn("WriteFile", names)

    def test_simulate_write_through_gate(self) -> None:
        guest = guest_from_pe(self.pe_path, process_id="win-notepad-1")
        fs = GovernedFS()
        ledger = Ledger(usl_node_id="usl-node-pe")
        gate = USLGate(ledger=ledger, fs=fs, sign=False)
        proc = GuestProcess(guest=guest, gate=gate)
        transition, _ = proc.simulate_write("C:/Users/jon/notes.txt", b"notepad")
        self.assertTrue(transition.crypto.event_hash)
        self.assertEqual(len(gate.ledger), 1)
        self.assertTrue(gate.ledger.verify_chain())
        self.assertEqual(fs.read("C:/Users/jon/notes.txt").decode("utf-8"), "notepad")


if __name__ == "__main__":
    unittest.main()
