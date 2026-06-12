"""USL CLI smoke commands."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def cmd_replay_transition(_args: argparse.Namespace) -> int:
    from src.usl.adapters.windows_fs import notepad_write_example
    from src.usl.gate import USLGate
    from src.usl.loaders.pe import guest_from_pe
    from src.usl.types import GuestAddressSpace, GuestContext, ImportSlot, UBO

    fixture = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "usl" / "minimal.pe"
    if fixture.exists():
        guest = guest_from_pe(fixture)
        guest.process_id = "notepad.exe"
    else:
        ubo = UBO(
            version="v1",
            binary_id="sha256:0000000000000000000000000000000000000000000000000000000000000001",
            os_family="windows",
            format="pe",
            entry_point=0x1000,
            segments=[],
            imports=[ImportSlot("KERNEL32.dll", "WriteFile", "kernel32.dll!writefile")],
        )
        guest = GuestContext(ubo=ubo, address_space=GuestAddressSpace(), process_id="notepad.exe")

    gate = USLGate()
    transition, result = notepad_write_example(guest, gate)
    print(json.dumps(transition.to_dict(), indent=2))
    if result:
        print("substrate:", json.dumps(result))
    print("ledger_events:", len(gate.ledger))
    return 0


def cmd_load_elf(args: argparse.Namespace) -> int:
    from src.usl.loaders.elf import load_elf

    ubo, _ = load_elf(args.path)
    print(json.dumps(ubo.to_dict(), indent=2))
    print("binary_id:", ubo.binary_id)
    return 0


def _fixture_elf_path() -> Path:
    staged = Path("/opt/cogos/lib/fixtures/usl/minimal.elf")
    if staged.is_file():
        return staged
    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "usl" / "minimal.elf"


def _lift_summary(model) -> dict:
    bindings_ceiling = model.capabilities.ceiling_id or "daily-driver"
    allowed: list[str] = []
    for res in model.capabilities.resources:
        if res.usl_capability_id:
            allowed.append(res.usl_capability_id)
    inv_rules = model.invariants.rules if model.invariants else []
    admission = [
        r.invariant_id
        for r in inv_rules
        if getattr(r, "severity", "info") in ("block", "warn")
    ]
    return {
        "program_id": model.meta.program_id,
        "binary_id": model.meta.binary_id,
        "profile_tier": bindings_ceiling,
        "allowed_capabilities": sorted(set(allowed)),
        "syscall_sites": len(model.effects.syscalls),
        "invariant_count": len(inv_rules),
        "admission_invariants": admission,
    }


def cmd_lift(args: argparse.Namespace) -> int:
    from src.usl.lift import lift_machine_code
    from src.usl.loaders.elf import load_elf

    ubo, _ = load_elf(args.path)
    model = lift_machine_code(ubo, source_path=str(args.path))
    summary = _lift_summary(model)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(model.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote lifted model: {out}", file=sys.stderr)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def cmd_forge(args: argparse.Namespace) -> int:
    from src.cloud_forge.types import LawEnvelope
    from src.usl.forge.compiler import ForgeCompiler
    from src.usl.lift import lift_machine_code
    from src.usl.loaders.elf import load_elf

    ubo, _ = load_elf(args.path)
    model = lift_machine_code(ubo, source_path=str(args.path))
    law = LawEnvelope(law_id=args.law_id, law_version=args.law_version)
    if args.mode == "static":
        root = Path(args.output) if args.output else Path.cwd() / "rootfs-staging"
        ref = ForgeCompiler.emit(
            model, mode="static", law=law, domain=args.domain, rootfs_dir=root
        )
        print(json.dumps(ref.to_dict(), indent=2, sort_keys=True))
        return 0
    bundle = ForgeCompiler.emit(model, mode="dynamic", law=law, domain=args.domain)
    payload = bundle.to_dict()
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote dynamic forge bundle: {out}", file=sys.stderr)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


_BROKER_SERVE_EPILOG = """\
Environment (runtime forge wiring):
  USL_FORGE_DIR   Directory with gate_policy.json (static forge bake)
  USL_LIFT_ELF    Lift binary at startup via ExokernelCourier (dynamic forge)
  USL_BROKER_ELF  Guest ELF path (default: staged minimal.elf fixture)
  USL_BROKER_SOCKET  AF_UNIX socket path
  USL_REGISTRY_DB SQLite artifact registry (optional; multi-guest persistence)
  USL_SUPERVISION_MODE  ipc (default) or ptrace for Slice 2.1 supervision
  USL_SUPERVISION_GUEST_ELF  ELF path when supervision mode is ptrace
  USL_SUPERVISION_GUEST_ID   guest_process_id for supervised traps
"""


def cmd_broker_serve(_args: argparse.Namespace) -> int:
    from src.usl.broker.server import serve_from_env

    serve_from_env()
    return 0


def _broker_smoke_syscall(args: argparse.Namespace, elf: Path) -> tuple[str, str, str, str]:
    """Pick capability/ceiling/path for broker smoke (containment vs daily-driver)."""
    import os

    from src.usl.forge.runtime_policy import load_forge_dir

    capability_id = "fs.write"
    ceiling_id = "fs.basic"
    path = args.path
    payload_b64 = ""

    forge_env = os.environ.get("USL_FORGE_DIR", "").strip()
    if forge_env:
        forge_path = Path(forge_env)
        if (forge_path / "gate_policy.json").is_file():
            policy = load_forge_dir(forge_path)
            if policy.profile_tier == "containment":
                capability_id = "fs.read"
                ceiling_id = "fs.readonly"
                path = elf.as_posix()
                return capability_id, ceiling_id, path, payload_b64

    import base64

    payload_b64 = base64.b64encode(args.data.encode("utf-8")).decode("ascii")
    return capability_id, ceiling_id, path, payload_b64


def cmd_broker_smoke(args: argparse.Namespace) -> int:
    from src.usl.broker.client import RemoteBroker
    from src.usl.broker.ipc import BrokerMessage
    from src.usl.law.default_policy import ALLOW
    from src.usl.loaders.elf import guest_from_elf

    elf = Path(args.elf) if args.elf else _fixture_elf_path()
    if not elf.is_file():
        print(f"fixture ELF missing: {elf}", file=sys.stderr)
        return 1

    guest = guest_from_elf(elf, process_id=args.process_id)
    broker = RemoteBroker()
    capability_id, ceiling_id, path, payload_b64 = _broker_smoke_syscall(args, elf)

    resp = broker.handle(
        BrokerMessage(
            msg_type="syscall",
            capability_id=capability_id,
            ceiling_id=ceiling_id,
            path=path,
            payload_b64=payload_b64,
            guest_process_id=guest.process_id,
            profile_id=guest.profile_id,
        )
    )
    substrate = resp.substrate or {}
    print("decision:", resp.decision)
    print("transition_id:", resp.transition_id)
    print("substrate:", json.dumps(substrate))

    if not resp.ok or resp.decision != ALLOW:
        return 1
    if capability_id == "fs.write":
        if substrate.get("bytes_written") != len(args.data.encode("utf-8")):
            return 1
    elif substrate.get("status") != "ok":
        return 1
    return 0


def cmd_serve_health(args: argparse.Namespace) -> int:
    health_path = Path(args.health_file)

    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path.split("?", 1)[0] != "/health":
                self.send_response(404)
                self.end_headers()
                return
            if health_path.is_file():
                body = health_path.read_text(encoding="utf-8").strip()
            else:
                body = json.dumps(
                    {"status": "degraded", "service": "usl", "runtime": "missing"},
                    sort_keys=True,
                )
            payload = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args) -> None:
            return

    server = ThreadingHTTPServer(("0.0.0.0", args.port), HealthHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
    return 0


def cmd_simulate_win_write(args: argparse.Namespace) -> int:
    from src.usl.gate import USLGate
    from src.usl.loaders.pe import GuestProcess, guest_from_pe

    guest = guest_from_pe(args.path)
    proc = GuestProcess(guest)
    gate = USLGate()
    path = args.output or "C:/Users/jon/test.txt"
    data = args.data.encode("utf-8") if args.data else b"hello"
    transition, result = proc.simulate_write(path, data, gate=gate)
    print(json.dumps(transition.to_dict(), indent=2))
    if result:
        print("substrate:", json.dumps(result))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="usl", description="USL CLI smoke tools")
    sub = parser.add_subparsers(dest="command", required=True)

    p_replay = sub.add_parser("replay-transition", help="Golden fs.write replay")
    p_replay.set_defaults(func=cmd_replay_transition)

    p_elf = sub.add_parser("load-elf", help="Load ELF fixture → UBO")
    p_elf.add_argument("--path", required=True)
    p_elf.set_defaults(func=cmd_load_elf)

    p_lift = sub.add_parser("lift", help="Lift ELF → ULLiftedModel summary")
    p_lift.add_argument("path", help="ELF binary path")
    p_lift.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write full lifted_model.json to this path",
    )
    p_lift.set_defaults(func=cmd_lift)

    p_forge = sub.add_parser("forge", help="Emit forge bundle from lifted ELF")
    p_forge.add_argument("path", help="ELF binary path")
    p_forge.add_argument(
        "--mode",
        choices=("dynamic", "static"),
        default="dynamic",
        help="dynamic: in-memory bundle; static: rootfs opt/cogos/usl-lifted artifacts",
    )
    p_forge.add_argument("--output", "-o", default=None, help="Output file or rootfs dir")
    p_forge.add_argument("--domain", default=None, help="Cloud forge domain slice")
    p_forge.add_argument("--law-id", default="usl-cli", dest="law_id")
    p_forge.add_argument("--law-version", default="1", dest="law_version")
    p_forge.set_defaults(func=cmd_forge)

    p_win = sub.add_parser("simulate-win-write", help="Simulate Windows fs.write")
    p_win.add_argument("--path", required=True, help="PE binary path")
    p_win.add_argument("--output", default=None)
    p_win.add_argument("--data", default="hello")
    p_win.set_defaults(func=cmd_simulate_win_write)

    p_bserve = sub.add_parser(
        "broker-serve",
        help="Unix-socket USL broker server",
        epilog=_BROKER_SERVE_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_bserve.set_defaults(func=cmd_broker_serve)

    p_bsmoke = sub.add_parser("broker-smoke", help="Fixture ELF write via RemoteBroker")
    p_bsmoke.add_argument("--elf", default=None, help="ELF fixture path")
    p_bsmoke.add_argument("--path", default="/tmp/usl-broker-smoke.txt")
    p_bsmoke.add_argument("--data", default="broker-smoke")
    p_bsmoke.add_argument("--process-id", default="usl-broker-guest")
    p_bsmoke.set_defaults(func=cmd_broker_smoke)

    p_health = sub.add_parser("serve-health", help="HTTP /health from JSON file")
    p_health.add_argument("--port", type=int, default=8766)
    p_health.add_argument("--health-file", required=True)
    p_health.set_defaults(func=cmd_serve_health)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
