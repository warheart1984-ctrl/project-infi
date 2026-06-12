from __future__ import annotations

import json
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path

from src.cloud_forge.types import LawEnvelope
from src.usl.broker.client import RemoteBroker
from src.usl.broker.ipc import BrokerMessage
from src.usl.broker.server import BrokerServer, BrokerServerConfig
from src.usl.forge.compiler import ForgeCompiler
from src.usl.lift import lift_machine_code
from src.usl.loaders.elf import load_elf
from tests.fixtures.usl.build_fixtures import ensure_fixtures


def _forge_dir_with_block_invariant(forge_dir: Path) -> None:
    """Patch lifted_model.json so compiler admission denies at broker boot."""
    lifted_path = forge_dir / "lifted_model.json"
    lifted = json.loads(lifted_path.read_text(encoding="utf-8"))
    rules = list(lifted.get("invariants", {}).get("rules") or [])
    rules.append(
        {
            "invariant_id": "inv-synthetic-block",
            "kind": "safety",
            "severity": "block",
            "description": "broker boot block test",
        }
    )
    lifted.setdefault("invariants", {})["rules"] = rules
    lifted_path.write_text(json.dumps(lifted, indent=2), encoding="utf-8")


@unittest.skipUnless(hasattr(socket, "AF_UNIX"), "AF_UNIX required")
class BrokerForgeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.elf_path, _ = ensure_fixtures()
        cls.law = LawEnvelope(law_id="test-law", law_version="1")
        ubo, _ = load_elf(cls.elf_path)
        cls.model = lift_machine_code(ubo, source_path=str(cls.elf_path))

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        root = Path(self._tmpdir.name)
        ForgeCompiler.emit(
            self.model,
            mode="static",
            law=self.law,
            rootfs_dir=root,
        )
        self.forge_dir = root / "opt" / "cogos" / "usl-lifted"
        self.sock_path = str(root / "broker.sock")
        self.pid_path = str(root / "broker.pid")
        config = BrokerServerConfig(
            socket_path=self.sock_path,
            pid_path=self.pid_path,
            elf_path=self.elf_path,
            guest_process_id="test-forge-guest",
            forge_dir=self.forge_dir,
        )
        self.server = BrokerServer(config=config)
        self._thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )
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

    def test_forge_policy_denies_fs_write(self) -> None:
        client = RemoteBroker(self.sock_path, timeout=5.0)
        msg = BrokerMessage(
            msg_type="syscall",
            capability_id="fs.write",
            ceiling_id="fs.basic",
            path="/broker/forge-test.txt",
            payload_b64="dGVzdA==",
            guest_process_id="test-forge-guest",
        )
        resp = client.handle(msg)
        self.assertFalse(resp.ok)
        self.assertEqual(resp.decision, "deny")


@unittest.skipUnless(hasattr(socket, "AF_UNIX"), "AF_UNIX required")
class BrokerForgeBlockedAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.elf_path, _ = ensure_fixtures()
        cls.law = LawEnvelope(law_id="test-law", law_version="1")
        ubo, _ = load_elf(cls.elf_path)
        cls.model = lift_machine_code(ubo, source_path=str(cls.elf_path))

    def test_broker_boot_denies_when_block_invariant_in_forge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ForgeCompiler.emit(
                self.model,
                mode="static",
                law=self.law,
                rootfs_dir=root,
            )
            forge_dir = root / "opt" / "cogos" / "usl-lifted"
            _forge_dir_with_block_invariant(forge_dir)
            config = BrokerServerConfig(
                socket_path=str(root / "broker.sock"),
                pid_path=str(root / "broker.pid"),
                elf_path=self.elf_path,
                guest_process_id="test-block-guest",
                forge_dir=forge_dir,
            )
            with self.assertRaises(RuntimeError) as ctx:
                BrokerServer(config=config)
            self.assertIn("inv-synthetic-block", str(ctx.exception))


@unittest.skipUnless(hasattr(socket, "AF_UNIX"), "AF_UNIX required")
class BrokerLegacyWithoutForgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.elf_path, _ = ensure_fixtures()

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        root = Path(self._tmpdir.name)
        self.sock_path = str(root / "broker.sock")
        self.pid_path = str(root / "broker.pid")
        config = BrokerServerConfig(
            socket_path=self.sock_path,
            pid_path=self.pid_path,
            elf_path=self.elf_path,
            guest_process_id="test-legacy-guest",
            forge_dir=None,
        )
        self.server = BrokerServer(config=config)
        self._thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )
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

    def test_legacy_broker_without_forge_still_allows(self) -> None:
        client = RemoteBroker(self.sock_path, timeout=5.0)
        msg = BrokerMessage(
            msg_type="syscall",
            capability_id="fs.write",
            ceiling_id="fs.basic",
            path="/broker/legacy.txt",
            payload_b64="dGVzdA==",
            guest_process_id="test-legacy-guest",
        )
        resp = client.handle(msg)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.decision, "allow")


if __name__ == "__main__":
    unittest.main()
