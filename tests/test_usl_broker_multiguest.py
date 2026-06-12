from __future__ import annotations

import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path

from src.usl.broker.client import RemoteBroker
from src.usl.broker.ipc import BrokerMessage
from src.usl.broker.server import BrokerServer, BrokerServerConfig
from tests.fixtures.usl.build_fixtures import ensure_fixtures


@unittest.skipUnless(hasattr(socket, "AF_UNIX"), "AF_UNIX required")
class BrokerMultiguestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.elf_path, _ = ensure_fixtures()

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.sock_path = str(Path(self._tmpdir.name) / "broker.sock")
        self.pid_path = str(Path(self._tmpdir.name) / "broker.pid")
        config = BrokerServerConfig(
            socket_path=self.sock_path,
            pid_path=self.pid_path,
            elf_path=Path(self.elf_path),
            guest_process_id="legacy-default-guest",
            forge_dir=None,
            allow_multiguest=True,
        )
        self.server = BrokerServer(config=config)
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()
        deadline = time.time() + 5.0
        while time.time() < deadline:
            if Path(self.sock_path).exists():
                break
            time.sleep(0.05)
        self.assertTrue(Path(self.sock_path).exists(), "broker socket not created")
        self.client = RemoteBroker(self.sock_path, timeout=5.0)

    def tearDown(self) -> None:
        self.server.shutdown()
        self._tmpdir.cleanup()

    def _register(
        self,
        guest_id: str,
        *,
        admission_state: str = "admitted",
    ) -> None:
        msg = BrokerMessage(
            msg_type="register_guest",
            guest_process_id=guest_id,
            path=self.elf_path,
            profile_id="usl-lifted-guest",
            extra={
                "elf_path": self.elf_path,
                "admission_state": admission_state,
            },
        )
        resp = self.client.handle(msg)
        self.assertTrue(resp.ok, resp.error or resp.decision)

    def test_two_guests_allow_and_deny(self) -> None:
        self._register("guest-allow", admission_state="admitted")
        self._register("guest-deny", admission_state="denied")

        allow_msg = BrokerMessage(
            msg_type="syscall",
            capability_id="fs.write",
            ceiling_id="fs.basic",
            path="/tmp/multiguest-allow.txt",
            payload_b64="dGVzdA==",
            guest_process_id="guest-allow",
        )
        allow_resp = self.client.handle(allow_msg)
        self.assertTrue(allow_resp.ok)
        self.assertEqual(allow_resp.decision, "allow")

        deny_msg = BrokerMessage(
            msg_type="syscall",
            capability_id="fs.write",
            ceiling_id="fs.basic",
            path="/tmp/multiguest-deny.txt",
            payload_b64="dGVzdA==",
            guest_process_id="guest-deny",
        )
        deny_resp = self.client.handle(deny_msg)
        self.assertFalse(deny_resp.ok)
        self.assertEqual(deny_resp.decision, "error")
        self.assertIn("guest_not_admitted", deny_resp.error or "")

    def test_unknown_guest_rejected_after_registration(self) -> None:
        self._register("guest-allow", admission_state="admitted")
        msg = BrokerMessage(
            msg_type="syscall",
            capability_id="fs.write",
            ceiling_id="fs.basic",
            path="/tmp/unknown.txt",
            payload_b64="",
            guest_process_id="guest-unknown",
        )
        resp = self.client.handle(msg)
        self.assertFalse(resp.ok)
        self.assertIn("unknown_guest", resp.error or "")


if __name__ == "__main__":
    unittest.main()
