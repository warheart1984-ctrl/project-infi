from __future__ import annotations

import argparse
import contextlib
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict

from plugins.prime_architect import PrimeArchitectPlugin
from runtime import SovereignIdeApiServer


@dataclass
class ConsoleIDEAPI:
    """Minimal IDE API used to exercise the scaffold."""

    commands: Dict[str, Callable[[], object]] = field(default_factory=dict)

    def register_command(self, name: str, handler: Callable[[], object]) -> None:
        self.commands[name] = handler


def build_runtime(*, ledger_path: str | None = None) -> dict[str, Any]:
    ide_api = ConsoleIDEAPI()
    if ledger_path is not None:
        os.environ["LEDGER_PATH"] = ledger_path
    plugin = PrimeArchitectPlugin(ide_api)
    plugin.activate()
    return {
        "ide_api": ide_api,
        "plugin": plugin,
        "ctx": plugin.ctx,
    }


def build_shell(runtime: dict[str, Any] | None = None) -> object:
    runtime = runtime or build_runtime()
    ide_api = runtime["ide_api"]
    command = ide_api.commands.get("sovereign.start")
    if command is None:
        raise RuntimeError("sovereign.start command was not registered")
    shell = command()
    if shell is None:
        raise RuntimeError("sovereign.start did not return a shell")
    return shell


def _print_bootstrap_summary(runtime: dict[str, Any]) -> None:
    print("sovereign-ide bootstrap complete")
    ctx = runtime["ctx"]
    if ctx is None:
        return
    for line in ctx.summary_lines():
        print(line)


def _serve_api(runtime: dict[str, Any], host: str, port: int) -> int:
    ctx = runtime["ctx"]
    if ctx is None:
        raise RuntimeError("runtime context was not bootstrapped")
    server = SovereignIdeApiServer(ctx, host=host, port=port)
    print(f"sovereign-ide api listening on {server.base_url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - manual run path
        return 130
    finally:
        with contextlib.suppress(Exception):
            server.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sovereign-ide")
    parser.add_argument(
        "--bootstrap-only",
        action="store_true",
        help="Boot the runtime without showing the shell",
    )
    parser.add_argument(
        "--serve-api",
        action="store_true",
        help="Expose the guided HTTP API hooks instead of opening the shell",
    )
    parser.add_argument(
        "--api-host",
        default="127.0.0.1",
        help="Host to bind the API server to",
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8787,
        help="Port to bind the API server to",
    )
    parser.add_argument(
        "--ledger-path",
        default=None,
        help="Override the LEDGER_PATH source used by the codex loader",
    )
    args = parser.parse_args(argv)

    runtime = build_runtime(ledger_path=args.ledger_path)
    if args.bootstrap_only:
        _print_bootstrap_summary(runtime)
        return 0
    if args.serve_api:
        return _serve_api(runtime, args.api_host, args.api_port)

    shell = build_shell(runtime)

    app = getattr(shell, "_app", None)
    if app is not None and hasattr(app, "exec"):
        return app.exec()
    return 0
