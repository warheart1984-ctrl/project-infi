from __future__ import annotations

import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path

from src.usl.broker.client import RemoteBroker
from src.usl.broker.server import BrokerServer, BrokerServerConfig
from src.usl.law.default_policy import ALLOW
from src.usl.loaders.elf import guest_from_elf, syscall_write
from tests.fixtures.usl.build_fixtures import ensure_fixtures


@unittest.skipUnless(hasattr(socket, "AF_UNIX"), "AF_UNIX required")
class BrokerIpcWriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.elf_path, _ = ensure_fixtures()

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.sock_path = str(Path(self._tmpdir.name) / "broker.sock")
        self.pid_path = str(Path(self._tmpdir.name) / "broker.pid")
        self.guest = guest_from_elf(self.elf_path, process_id="ipc-write-guest")
        config = BrokerServerConfig(
            socket_path=self.sock_path,
            pid_path=self.pid_path,
            elf_path=self.elf_path,
            guest_process_id="ipc-write-guest",
        )
        self.server = BrokerServer(guest=self.guest, config=config)
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()
        deadline = time.time() + 5.0
        while time.time() < deadline:
            if Path(self.sock_path).exists():
                break
            time.sleep(0.05)
        self.assertTrue(Path(self.sock_path).exists())

    def tearDown(self) -> None:
        self.server.shutdown()
        self._tmpdir.cleanup()

    def test_syscall_write_via_remote_broker(self) -> None:
        broker = RemoteBroker(self.sock_path, timeout=5.0)
        payload = b"ipc-broker-data"
        transition, substrate = syscall_write(
            self.guest,
            "/tmp/usl-broker-ipc.txt",
            payload,
            None,
            broker=broker,
        )
        self.assertEqual(transition.law.decision, ALLOW)
        self.assertIsNotNone(substrate)
        self.assertEqual(substrate.get("bytes_written"), len(payload))
        self.assertGreater(len(self.server.gate.ledger), 0)


if __name__ == "__main__":
    unittest.main()
