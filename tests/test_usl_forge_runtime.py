from __future__ import annotations

import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from src.cloud_forge.types import LawEnvelope
from src.usl.forge.compiler import ForgeCompiler
from src.usl.forge.runtime_policy import (
    check_admission,
    evaluate_capability,
    load_forge_dir,
    resolve_syscall_capability,
)
from src.usl.law.default_policy import ALLOW, DENY
from src.usl.lift import lift_machine_code
from src.usl.loaders.elf import guest_from_elf, load_elf
from src.usl.types import CapabilityRequest, DeltaSummary, ResourceInfo
from tests.fixtures.usl.build_fixtures import ensure_fixtures


class ForgeRuntimePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.elf_path, _ = ensure_fixtures()
        cls.law = LawEnvelope(law_id="test-law", law_version="1")
        ubo, _ = load_elf(cls.elf_path)
        cls.model = lift_machine_code(ubo, source_path=str(cls.elf_path))

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        ForgeCompiler.emit(
            self.model,
            mode="static",
            law=self.law,
            rootfs_dir=self.root,
        )
        self.forge_dir = self.root / "opt" / "cogos" / "usl-lifted"

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_load_forge_dir_profile_tier(self) -> None:
        policy = load_forge_dir(self.forge_dir)
        self.assertEqual(policy.profile_tier, "containment")

    def test_evaluate_capability_denies_fs_write_under_containment(self) -> None:
        policy = load_forge_dir(self.forge_dir)
        guest = guest_from_elf(self.elf_path)
        guest.profile_id = policy.profile_tier
        request = CapabilityRequest(
            capability_id="fs.write",
            ceiling_id="fs.basic",
            resource=ResourceInfo(kind="file", locator="/tmp/test.txt"),
            guest=guest,
            pre_state_hash="pre",
            post_state_hash="post",
            delta_hash="delta",
            delta_summary=DeltaSummary(bytes_written=4),
        )
        decision = evaluate_capability(request, policy)
        self.assertEqual(decision.decision, DENY)
        self.assertIn("ceiling", decision.decision_reason)

    def test_check_admission_blocks_on_block_severity(self) -> None:
        policy = load_forge_dir(self.forge_dir)
        blocked_model = dict(policy.lifted_model or {})
        rules = list(blocked_model.get("invariants", {}).get("rules") or [])
        rules.append({"invariant_id": "inv-block-test", "severity": "block"})
        blocked_model["invariants"] = {"rules": rules}
        gate = dict(policy.gate_policy)
        gate["admission_invariants"] = list(
            gate.get("admission_invariants") or []
        ) + ["inv-block-test"]
        policy2 = replace(policy, gate_policy=gate, lifted_model=blocked_model)
        ok, reason = check_admission(policy2, lifted_model=blocked_model)
        self.assertFalse(ok)
        self.assertIn("inv-block-test", reason)

    def test_check_admission_compiler_blocks_block_severity_in_model_only(self) -> None:
        prev = os.environ.get("USL_GOVERNANCE_ADMISSION")
        os.environ["USL_GOVERNANCE_ADMISSION"] = "compiler"
        try:
            policy = load_forge_dir(self.forge_dir)
            self.assertIsNotNone(policy.governance_decode_bundle)
            blocked_model = dict(policy.lifted_model or {})
            rules = list(blocked_model.get("invariants", {}).get("rules") or [])
            rules.append(
                {
                    "invariant_id": "inv-compiler-only-block",
                    "kind": "safety",
                    "severity": "block",
                }
            )
            blocked_model.setdefault("invariants", {})["rules"] = rules
            ok, reason = check_admission(policy, lifted_model=blocked_model)
            self.assertFalse(ok)
            self.assertIn("inv-compiler-only-block", reason)
        finally:
            if prev is None:
                os.environ.pop("USL_GOVERNANCE_ADMISSION", None)
            else:
                os.environ["USL_GOVERNANCE_ADMISSION"] = prev

    def test_evaluate_capability_allows_fs_read_under_containment(self) -> None:
        policy = load_forge_dir(self.forge_dir)
        guest = guest_from_elf(self.elf_path)
        guest.profile_id = policy.profile_tier
        request = CapabilityRequest(
            capability_id="fs.read",
            ceiling_id="fs.readonly",
            resource=ResourceInfo(kind="file", locator=self.elf_path),
            guest=guest,
            pre_state_hash="pre",
            post_state_hash="post",
            delta_hash="delta",
            delta_summary=DeltaSummary(),
        )
        decision = evaluate_capability(request, policy)
        self.assertEqual(decision.decision, ALLOW)

    def test_resolve_syscall_capability_unknown_confidence(self) -> None:
        policy = load_forge_dir(self.forge_dir)
        policy2 = replace(
            policy,
            broker_profile={
                "syscall_mappings": [
                    {
                        "syscall_number": 1,
                        "confidence": "unknown",
                        "usl_capability_id": "fs.write",
                    }
                ]
            },
        )
        self.assertIsNone(resolve_syscall_capability(policy2, 1))


if __name__ == "__main__":
    unittest.main()
