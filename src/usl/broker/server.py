"""Unix-domain-socket broker server — NDJSON framing over GuestBroker."""

from __future__ import annotations

import os
import socket
import threading
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

from src.usl.broker.ipc import BrokerMessage, BrokerResponse
from src.usl.broker.supervisor import GuestBroker
from src.usl.gate import USLGate
from src.usl.loaders.elf import guest_from_elf
from src.usl.types import GuestContext

if TYPE_CHECKING:
    pass

DEFAULT_SOCKET = "/run/cog/usl-broker.sock"
DEFAULT_PID_FILE = "/run/cog/usl-broker.pid"
DEFAULT_ELF_FIXTURE = "/opt/cogos/lib/fixtures/usl/minimal.elf"


def default_socket_path() -> str:
    return os.environ.get("USL_BROKER_SOCKET", DEFAULT_SOCKET)


def default_pid_path() -> str:
    run = os.environ.get("COG_RUN_DIR", "/run/cog")
    return os.environ.get("USL_BROKER_PID", f"{run}/usl-broker.pid")


def _default_elf_path() -> Path:
    env = os.environ.get("USL_BROKER_ELF")
    if env:
        return Path(env)
    staged = Path(DEFAULT_ELF_FIXTURE)
    if staged.is_file():
        return staged
    repo = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "usl" / "minimal.elf"
    return repo


@dataclass
class BrokerServerConfig:
    socket_path: str = ""
    pid_path: str = ""
    elf_path: Path | None = None
    guest_process_id: str = "usl-broker-guest"
    forge_dir: Path | None = None
    lift_elf: Path | None = None
    law_envelope_id: str = "usl-runtime"
    allow_multiguest: bool = True


@dataclass
class GuestRoute:
    """Per-guest routing entry (Slice 2.1+ multi-guest broker)."""

    guest_process_id: str
    elf_path: str = ""
    profile_id: str = "usl-lifted-guest"
    admission_state: str = "admitted"
    forge_dir: Path | None = None


class BrokerServer:
    """AF_UNIX listener; one JSON object per line in/out."""

    def __init__(
        self,
        gate: USLGate | None = None,
        guest: GuestContext | None = None,
        *,
        config: BrokerServerConfig | None = None,
    ) -> None:
        self.config = config or BrokerServerConfig()
        self.socket_path = self.config.socket_path or default_socket_path()
        self.pid_path = self.config.pid_path or default_pid_path()

        elf = self.config.elf_path or _default_elf_path()
        forge_dir = self.config.forge_dir
        lift_elf = self.config.lift_elf
        if forge_dir is None:
            env_forge = os.environ.get("USL_FORGE_DIR")
            if env_forge:
                candidate = Path(env_forge)
                if (candidate / "gate_policy.json").is_file():
                    forge_dir = candidate
        if lift_elf is None:
            env_lift = os.environ.get("USL_LIFT_ELF")
            if env_lift:
                lift_elf = Path(env_lift)

        forge_policy = None
        if forge_dir is not None or lift_elf is not None:
            from src.usl.forge.bootstrap import bootstrap_forge_runtime

            boot = bootstrap_forge_runtime(
                elf,
                forge_dir=forge_dir,
                lift_elf=lift_elf,
                guest=guest,
            )
            self._guest = boot.guest
            forge_policy = boot.forge_policy
        elif guest is not None:
            self._guest = guest
        else:
            self._guest = guest_from_elf(
                elf, process_id=self.config.guest_process_id
            )

        if gate is not None:
            self._gate = gate
            if forge_policy is not None and gate.forge_policy is None:
                gate.forge_policy = forge_policy
        else:
            self._gate = USLGate(sign=False, forge_policy=forge_policy)

        forge_policy = forge_policy or getattr(self._gate, "forge_policy", None)
        self._broker = GuestBroker(
            self._gate, self._guest, forge_policy=forge_policy
        )
        self._routes: dict[str, GuestRoute] = {}
        self._guest_brokers: dict[str, GuestBroker] = {}
        self._default_elf = elf
        self._default_forge_dir = forge_dir
        self._sock: socket.socket | None = None
        self._stop = threading.Event()

    @property
    def gate(self) -> USLGate:
        return self._gate

    @property
    def guest(self) -> GuestContext:
        return self._guest

    def _error_response(self, error: str) -> str:
        return BrokerResponse(ok=False, decision="error", error=error).to_json() + "\n"

    def register_guest(self, route: GuestRoute) -> BrokerResponse:
        """Register a guest in the routing table (also used by IPC ``register_guest``)."""
        if not route.guest_process_id:
            return BrokerResponse(ok=False, decision="error", error="missing_guest_id")
        self._routes[route.guest_process_id] = route
        if route.admission_state != "admitted":
            return BrokerResponse(ok=True, decision="allow", transition_id="register_denied_state")
        broker = self._broker_for_route(route)
        if broker is not None:
            self._guest_brokers[route.guest_process_id] = broker
        return BrokerResponse(ok=True, decision="allow", transition_id="register_guest")

    def _broker_for_route(self, route: GuestRoute) -> GuestBroker | None:
        elf = Path(route.elf_path) if route.elf_path else self._default_elf
        if not elf.is_file():
            return None
        forge_dir = route.forge_dir or self._default_forge_dir
        lift_elf = None
        forge_policy = None
        guest = guest_from_elf(elf, process_id=route.guest_process_id)
        guest = replace(guest, profile_id=route.profile_id)
        if forge_dir is not None:
            from src.usl.forge.bootstrap import bootstrap_forge_runtime

            boot = bootstrap_forge_runtime(
                elf,
                forge_dir=forge_dir,
                lift_elf=lift_elf,
                guest=guest,
            )
            guest = boot.guest
            forge_policy = boot.forge_policy
        gate = USLGate(sign=False, forge_policy=forge_policy)
        return GuestBroker(gate, guest, forge_policy=forge_policy)

    def _handle_register_guest(self, msg: BrokerMessage) -> BrokerResponse:
        extra = msg.extra or {}
        forge_raw = str(extra.get("forge_dir") or "").strip()
        route = GuestRoute(
            guest_process_id=msg.guest_process_id or str(extra.get("guest_process_id") or ""),
            elf_path=str(extra.get("elf_path") or msg.path or ""),
            profile_id=msg.profile_id or str(extra.get("profile_id") or "usl-lifted-guest"),
            admission_state=str(extra.get("admission_state") or "admitted"),
            forge_dir=Path(forge_raw) if forge_raw else None,
        )
        return self.register_guest(route)

    def _resolve_broker(self, msg: BrokerMessage) -> GuestBroker:
        guest_id = msg.guest_process_id or self.config.guest_process_id
        if self._routes and self.config.allow_multiguest:
            route = self._routes.get(guest_id)
            if route is None:
                raise ValueError(f"unknown_guest:{guest_id}")
            if route.admission_state != "admitted":
                raise ValueError(f"guest_not_admitted:{guest_id}")
            if guest_id in self._guest_brokers:
                return self._guest_brokers[guest_id]
            if route.profile_id and not msg.profile_id:
                msg = replace(msg, profile_id=route.profile_id)
        elif guest_id in self._guest_brokers:
            return self._guest_brokers[guest_id]
        return self._broker

    def _handle_line(self, line: bytes) -> bytes:
        stripped = line.strip()
        if not stripped:
            return self._error_response("empty_line").encode("utf-8")
        try:
            msg = BrokerMessage.from_json(stripped)
        except Exception as exc:
            return self._error_response(str(exc)[:500]).encode("utf-8")
        if msg.msg_type == "register_guest":
            return (self._handle_register_guest(msg).to_json() + "\n").encode("utf-8")
        try:
            broker = self._resolve_broker(msg)
        except ValueError as exc:
            return self._error_response(str(exc)).encode("utf-8")
        return (broker.handle(msg).to_json() + "\n").encode("utf-8")

    def _serve_client(self, conn: socket.socket) -> None:
        buffer = b""
        try:
            while not self._stop.is_set():
                chunk = conn.recv(65536)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    conn.sendall(self._handle_line(line))
        finally:
            conn.close()

    def prepare_socket(self) -> None:
        path = Path(self.socket_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            path.unlink()
        pid_parent = Path(self.pid_path).parent
        pid_parent.mkdir(parents=True, exist_ok=True)

    def write_pid(self) -> None:
        Path(self.pid_path).write_text(f"{os.getpid()}\n", encoding="utf-8")

    def remove_pid(self) -> None:
        try:
            Path(self.pid_path).unlink(missing_ok=True)
        except OSError:
            pass

    def serve_forever(self) -> None:
        self.prepare_socket()
        self.write_pid()
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock = sock
        try:
            sock.bind(self.socket_path)
            # World-writable so broker-smoke (same rc daemon user) can connect in minimal images.
            os.chmod(self.socket_path, 0o666)
            sock.listen(8)
            while not self._stop.is_set():
                try:
                    conn, _ = sock.accept()
                except OSError:
                    if self._stop.is_set():
                        break
                    raise
                threading.Thread(
                    target=self._serve_client,
                    args=(conn,),
                    daemon=True,
                ).start()
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        self._stop.set()
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        try:
            Path(self.socket_path).unlink(missing_ok=True)
        except OSError:
            pass
        self.remove_pid()


def serve_from_env() -> None:
    """CLI entry: block until interrupted."""
    server = BrokerServer()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
