from __future__ import annotations

import unittest

from src.usl.canonical_serialize import event_hash, ledger_root
from src.usl.voss_ledger import GENESIS_ROOT, Ledger
from tests.test_usl_canonical_serialize import _golden_transition


class LedgerTests(unittest.TestCase):
    def test_append_updates_chain(self) -> None:
        ledger = Ledger(usl_node_id="usl-node-test")
        t1 = _golden_transition()
        t2 = _golden_transition()
        t2.transition_id = "00000000-0000-4000-8000-000000000002"

        ledger.append(t1, sign=False)
        ledger.append(t2, sign=False)

        self.assertEqual(len(ledger), 2)
        self.assertEqual(t1.crypto.prev_ledger_root, GENESIS_ROOT)
        self.assertEqual(t1.crypto.event_hash, event_hash(t1))
        self.assertEqual(
            t1.crypto.ledger_root,
            ledger_root(GENESIS_ROOT, t1.crypto.event_hash),
        )
        self.assertEqual(t2.crypto.prev_ledger_root, t1.crypto.ledger_root)
        self.assertEqual(ledger.root, t2.crypto.ledger_root)

    def test_verify_chain_passes(self) -> None:
        ledger = Ledger(usl_node_id="usl-node-test")
        for i in range(3):
            t = _golden_transition()
            t.transition_id = f"00000000-0000-4000-8000-00000000000{i}"
            ledger.append(t, sign=False)
        self.assertTrue(ledger.verify_chain())

    def test_tamper_detection(self) -> None:
        ledger = Ledger(usl_node_id="usl-node-test")
        t = _golden_transition()
        ledger.append(t, sign=False)
        t.crypto.event_hash = "sha256:" + "f" * 64
        self.assertFalse(ledger.verify_chain())


if __name__ == "__main__":
    unittest.main()
