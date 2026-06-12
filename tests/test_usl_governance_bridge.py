from __future__ import annotations

import json
import os
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from src.cloud_forge.types import LawEnvelope
from src.usl.forge.compiler import ForgeCompiler
from src.usl.forge.runtime_policy import check_admission, load_forge_dir
from src.usl.lift.governance_bridge import (
    compile_lift_governance,
    run_lift_admission,
    run_lift_admission_from_dict,
)
from src.usl.lift import lift_machine_code
from src.usl.loaders.elf import load_elf
from tests.fixtures.usl.build_fixtures import ensure_fixtures, ensure_syscall_elf


class GovernanceBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.elf_path, _ = ensure_fixtures()
        cls.law = LawEnvelope(law_id="test-law", law_version="1")
        ubo, _ = load_elf(cls.elf_path)
        cls.model = lift_machine_code(ubo, source_path=str(cls.elf_path))

    def test_info_invariant_admitted_under_compiler_path(self) -> None:
        bundle = compile_lift_governance(self.model, law_bundle={"law_id": "test"})
        outcome = run_lift_admission(self.model, bundle)
        self.assertTrue(outcome.get("allows", False))
        self.assertTrue(
            any(
                r.get("validator") == "lift_binary_invariant" and r.get("status") == "pass"
                for r in outcome.get("results") or []
                if isinstance(r, dict)
            )
        )

    def test_block_invariant_denies_admission(self) -> None:
        from dataclasses import replace

        from src.usl.lift.types import AAISInvariantRule, AAISInvariantSet

        blocked_rules = list(self.model.invariants.rules) + [
            AAISInvariantRule(
                invariant_id="inv-synthetic-block",
                kind="safety",
                severity="block",
                description="test block",
            )
        ]
        blocked_model = replace(
            self.model,
            invariants=AAISInvariantSet(rules=blocked_rules),
        )
        bundle = compile_lift_governance(blocked_model)
        outcome = run_lift_admission(blocked_model, bundle)
        self.assertFalse(outcome.get("allows", True))
        blocked = next(
            (
                r
                for r in outcome.get("results") or []
                if isinstance(r, dict) and r.get("validator") == "lift_binary_invariant"
            ),
            None,
        )
        self.assertIsNotNone(blocked)
        assert blocked is not None
        self.assertEqual(blocked.get("status"), "fail")
        self.assertIn("inv-synthetic-block", blocked.get("blocked_invariants") or [])

    def test_static_forge_round_trip_admission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ForgeCompiler.emit(
                self.model,
                mode="static",
                law=self.law,
                rootfs_dir=root,
            )
            forge_dir = root / "opt" / "cogos" / "usl-lifted"
            policy = load_forge_dir(forge_dir)
            self.assertIsNotNone(policy.governance_decode_bundle)
            ok, reason = check_admission(policy)
            self.assertTrue(ok, msg=reason)

    def test_compiler_path_from_serialized_model(self) -> None:
        syscall_elf = ensure_syscall_elf()
        ubo, _ = load_elf(syscall_elf)
        model = lift_machine_code(ubo, source_path=str(syscall_elf))
        lifted = model.to_dict()
        bundle = compile_lift_governance(model)
        with unittest.mock.patch.dict(os.environ, {"USL_GOVERNANCE_ADMISSION": "compiler"}):
            outcome = run_lift_admission_from_dict(lifted, bundle)
        self.assertTrue(outcome.get("allows", False))


if __name__ == "__main__":
    unittest.main()
