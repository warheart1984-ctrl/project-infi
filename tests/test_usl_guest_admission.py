"""Guest-safe lift admission (stdlib path; no networkx)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.usl.lift.guest_admission import run_lift_admission_from_dict

_FIXTURE_DIR = (
    Path(__file__).resolve().parents[1]
    / "cog-os"
    / "forge"
    / "fixtures"
    / "usl-lifted"
)


def _load_fixture(name: str) -> dict:
    return json.loads((_FIXTURE_DIR / name).read_text(encoding="utf-8"))


class GuestAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.decode_bundle = _load_fixture("governance_decode_bundle.json")
        self.lifted_model = _load_fixture("lifted_model.json")

    def test_empty_rules_admits(self) -> None:
        model = dict(self.lifted_model)
        model["invariants"] = {"rules": []}
        outcome = run_lift_admission_from_dict(model, self.decode_bundle)
        self.assertTrue(outcome["allows"])
        self.assertEqual(outcome["status"], "pass")

    def test_warn_only_admits(self) -> None:
        model = dict(self.lifted_model)
        rules = list(model.get("invariants", {}).get("rules") or [])
        rules.append(
            {
                "invariant_id": "inv-warn-only",
                "kind": "safety",
                "severity": "warn",
            }
        )
        model["invariants"] = {"rules": rules}
        outcome = run_lift_admission_from_dict(model, self.decode_bundle)
        self.assertTrue(outcome["allows"])

    def test_block_severity_denies(self) -> None:
        model = dict(self.lifted_model)
        rules = list(model.get("invariants", {}).get("rules") or [])
        rules.append(
            {
                "invariant_id": "inv-block-guest",
                "kind": "safety",
                "severity": "block",
            }
        )
        model["invariants"] = {"rules": rules}
        outcome = run_lift_admission_from_dict(model, self.decode_bundle)
        self.assertFalse(outcome["allows"])
        self.assertEqual(outcome["status"], "fail")
        lift_result = next(
            r
            for r in outcome["results"]
            if r.get("validator") == "lift_binary_invariant"
        )
        self.assertIn("inv-block-guest", lift_result.get("blocked_invariants") or [])

    def test_outcome_shape(self) -> None:
        outcome = run_lift_admission_from_dict(self.lifted_model, self.decode_bundle)
        self.assertEqual(outcome["module_id"], "aais.invariant_compiler.admission")
        self.assertIn("status", outcome)
        self.assertIn("allows", outcome)
        self.assertIsInstance(outcome["results"], list)
        self.assertTrue(outcome["results"])


if __name__ == "__main__":
    unittest.main()
