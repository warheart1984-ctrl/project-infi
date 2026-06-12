"""Remote broker client over Unix domain socket."""

from __future__ import annotations

import os
import socket
from typing import TYPE_CHECKING

from src.usl.broker.ipc import BrokerMessage, BrokerResponse
from src.usl.broker.server import default_socket_path

if TYPE_CHECKING:
    pass

DEFAULT_TIMEOUT = 30.0


class RemoteBroker:
    """Same surface as GuestBroker: handle(msg) -> BrokerResponse."""

    def __init__(
        self,
        socket_path: str | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.socket_path = socket_path or default_socket_path()
        self.timeout = timeout

    def handle(self, message: BrokerMessage) -> BrokerResponse:
        raw = (message.to_json() + "\n").encode("utf-8")
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect(self.socket_path)
                sock.sendall(raw)
                buffer = b""
                while b"\n" not in buffer:
                    chunk = sock.recv(65536)
                    if not chunk:
                        break
                    buffer += chunk
                line = buffer.split(b"\n", 1)[0].strip()
                if not line:
                    return BrokerResponse(
                        ok=False,
                        decision="error",
                        error="broker_disconnect",
                    )
                return BrokerResponse.from_json(line)
        except FileNotFoundError:
            return BrokerResponse(
                ok=False,
                decision="error",
                error=f"broker_socket_missing:{self.socket_path}",
            )
        except OSError as exc:
            return BrokerResponse(
                ok=False,
                decision="error",
                error=f"broker_io:{exc}"[:500],
            )
        except Exception as exc:
            return BrokerResponse(
                ok=False,
                decision="error",
                error=str(exc)[:500],
            )

    def ping(self) -> bool:
        """Return True if socket exists and accepts connections."""
        if not os.path.exists(self.socket_path):
            return False
        msg = BrokerMessage(
            msg_type="syscall",
            capability_id="fs.stat",
            ceiling_id="fs.basic",
            path="/",
        )
        resp = self.handle(msg)
        return resp.decision != "error" or resp.error != "broker_socket_missing:" + self.socket_path
