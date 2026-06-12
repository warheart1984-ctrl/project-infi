from __future__ import annotations

import os
import unittest

from src.usl.broker.ipc import BrokerMessage, BrokerResponse
from src.usl.supervision.config import SupervisionConfig, load_supervision_config
from src.usl.supervision.runner import SupervisionRunner
from src.usl.supervision.seccomp import describe_seccomp_policy, seccomp_available
from tests.fixtures.usl.build_fixtures import ensure_fixtures


class SupervisionConfigTests(unittest.TestCase):
    def test_default_mode_ipc(self) -> None:
        old = os.environ.pop("USL_SUPERVISION_MODE", None)
        try:
            cfg = load_supervision_config()
            self.assertEqual(cfg.mode, "ipc")
        finally:
            if old is not None:
                os.environ["USL_SUPERVISION_MODE"] = old

    def test_ptrace_mode_from_env(self) -> None:
        old = os.environ.get("USL_SUPERVISION_MODE")
        os.environ["USL_SUPERVISION_MODE"] = "ptrace"
        try:
            cfg = load_supervision_config()
            self.assertEqual(cfg.mode, "ptrace")
        finally:
            if old is None:
                os.environ.pop("USL_SUPERVISION_MODE", None)
            else:
                os.environ["USL_SUPERVISION_MODE"] = old


class SupervisionRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.elf_path, _ = ensure_fixtures()

    def test_smoke_once_routes_through_broker_handler(self) -> None:
        runner = SupervisionRunner(
            config=SupervisionConfig(
                mode="ptrace",
                guest_elf=self.elf_path,
                guest_process_id="supervision-smoke-guest",
            )
        )

        def handler(msg: BrokerMessage) -> BrokerResponse:
            self.assertEqual(msg.guest_process_id, "supervision-smoke-guest")
            self.assertEqual(msg.extra.get("supervision"), "ptrace")
            return BrokerResponse(ok=True, decision="allow", transition_id="t-supervision")

        runner.attach_broker(handler)
        resp = runner.smoke_once()
        self.assertTrue(resp.ok)
        self.assertEqual(resp.decision, "allow")
        self.assertEqual(runner.state.traps_handled, 1)

    def test_policy_summary(self) -> None:
        runner = SupervisionRunner(
            config=SupervisionConfig(mode="ipc", guest_process_id="ipc-guest")
        )
        summary = runner.policy_summary()
        self.assertEqual(summary["mode"], "ipc")
        self.assertIn("default", summary["seccomp"])

    def test_start_guest_requires_ptrace_and_linux(self) -> None:
        runner = SupervisionRunner(
            config=SupervisionConfig(mode="ipc", guest_elf=self.elf_path)
        )
        with self.assertRaises(RuntimeError):
            runner.start_guest()


class SeccompPolicyTests(unittest.TestCase):
    def test_describe_policy(self) -> None:
        policy = describe_seccomp_policy()
        self.assertEqual(policy["default"], "deny")

    def test_seccomp_available_on_linux_ci(self) -> None:
        if os.name == "posix" and os.uname().sysname == "Linux":
            self.assertTrue(seccomp_available())


if __name__ == "__main__":
    unittest.main()
