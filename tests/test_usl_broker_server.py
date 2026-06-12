from __future__ import annotations

import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path

from src.usl.broker.ipc import BrokerMessage, BrokerResponse
from src.usl.broker.server import BrokerServer, BrokerServerConfig
from src.usl.broker.client import RemoteBroker
from tests.fixtures.usl.build_fixtures import ensure_fixtures


@unittest.skipUnless(hasattr(socket, "AF_UNIX"), "AF_UNIX required")
class BrokerServerTests(unittest.TestCase):
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
            elf_path=self.elf_path,
            guest_process_id="test-broker-guest",
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

    def tearDown(self) -> None:
        self.server.shutdown()
        self._tmpdir.cleanup()

    def test_round_trip_fs_write(self) -> None:
        client = RemoteBroker(self.sock_path, timeout=5.0)
        msg = BrokerMessage(
            msg_type="syscall",
            capability_id="fs.write",
            ceiling_id="fs.basic",
            path="/broker/test.txt",
            payload_b64="dGVzdA==",
            guest_process_id="test-broker-guest",
        )
        resp = client.handle(msg)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.decision, "allow")
        self.assertTrue(resp.transition_id)
        self.assertIsNotNone(resp.substrate)

    def test_malformed_line_returns_error(self) -> None:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(5.0)
            sock.connect(self.sock_path)
            sock.sendall(b"not-json\n")
            buffer = b""
            while b"\n" not in buffer:
                chunk = sock.recv(4096)
                self.assertTrue(chunk)
                buffer += chunk
            line = buffer.split(b"\n", 1)[0]
            resp = BrokerResponse.from_json(line)
            self.assertFalse(resp.ok)
            self.assertEqual(resp.decision, "error")


if __name__ == "__main__":
    unittest.main()
