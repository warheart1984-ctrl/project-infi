"""Brain layer runtime tests."""

from __future__ import annotations

import unittest

from src.brain_layer_runtime import build_brain_status, propose


class BrainLayerRuntimeTests(unittest.TestCase):
    def test_status_and_propose(self):
        status = build_brain_status()
        self.assertEqual(status["status"], "proposal_only")
        result = propose("research brief")
        self.assertTrue(result["ok"])
        self.assertEqual(result["proposal"]["status"], "proposal_only")


if __name__ == "__main__":
    unittest.main()
