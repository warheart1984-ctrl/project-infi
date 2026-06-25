"""Repo-local Nova CLI for the Lawful Nova runtime slice."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from nova.runtime_factory import build_lawful_llm, collect_runtime_health


@dataclass(frozen=True)
class Check:
    status: str
    detail: str = ""


def _http_health(url: str) -> Check:
    try:
        request = Request(url.rstrip("/") + "/health", headers={"Accept": "application/json"})
        with urlopen(request, timeout=2) as response:
            body = response.read().decode("utf-8", errors="replace")
        return Check(status="ok", detail=body)
    except (OSError, URLError) as exc:
        return Check(status="warn", detail=str(exc))


def collect_health() -> dict[str, Any]:
    direct_status = "ok"
    direct_detail = ""
    runtime_health: dict[str, Any] = {}
    try:
        runtime_health = collect_runtime_health()
        llm = build_lawful_llm(operator_session_id="nova-local-cli", signing_secret="local-dev-secret")
        turn = llm.ask("observe lawful nova health", tenant_id="local", capability="observe")
        direct_detail = turn.voss_runtime["decision"]
    except Exception as exc:  # pragma: no cover - defensive diagnostic
        direct_status = "fail"
        direct_detail = str(exc)

    return {
        "service": "nova_local_cli",
        "repo_root": str(Path.cwd()),
        **runtime_health,
        "direct_lawful_llm": asdict(Check(status=direct_status, detail=direct_detail)),
        "lawful_brain_api": asdict(_http_health("http://127.0.0.1:8791")),
        "operator_kernel_api": asdict(_http_health("http://127.0.0.1:8790")),
    }


def _print(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, sort_keys=True))
        return
    for key, value in payload.items():
        if isinstance(value, dict):
            print(f"{key}: {value.get('status')} {value.get('detail', '')}".rstrip())
        else:
            print(f"{key}: {value}")


def health_command(args: argparse.Namespace) -> int:
    payload = collect_health()
    _print(payload, as_json=args.json)
    return 0 if payload["direct_lawful_llm"]["status"] == "ok" else 1


def ask_command(args: argparse.Namespace) -> int:
    llm = build_lawful_llm(operator_session_id="nova-local-cli", signing_secret="local-dev-secret")
    turn = llm.ask(
        args.prompt,
        tenant_id=args.tenant,
        capability=args.capability,
    )
    payload = {
        "text": turn.text,
        "receipt_verified": llm.verify_receipt(turn.receipt),
        "decision": turn.voss_runtime["decision"],
    }
    _print(payload, as_json=args.json)
    return 0


def serve_command(args: argparse.Namespace) -> int:
    from nova.api import main

    main()
    return 0


def _kernel_base() -> str:
    return os.environ.get("OPERATOR_KERNEL_URL", "http://127.0.0.1:8790").rstrip("/")


def _kernel_json(method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    import json as _json
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen

    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = _json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(f"{_kernel_base()}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return _json.loads(raw) if raw.strip() else {}
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(detail or str(exc)) from exc


def plan_command(args: argparse.Namespace) -> int:
    payload = _kernel_json(
        "POST",
        "/agent/tasks",
        {
            "goal": args.prompt,
            "constraints": {
                "read_only": True,
                "allow_shell": False,
                "allow_git_commit": False,
                "allow_network": False,
                "max_steps": 1,
            },
        },
    )
    _print(payload, as_json=args.json)
    return 0


def task_list_command(args: argparse.Namespace) -> int:
    payload = _kernel_json("GET", "/agent/tasks")
    _print(payload, as_json=args.json)
    return 0


def task_resume_command(args: argparse.Namespace) -> int:
    payload = _kernel_json(
        "POST",
        f"/agent/tasks/{args.task_id}/message",
        {"text": args.message},
    )
    _print(payload, as_json=args.json)
    return 0


def open_command(args: argparse.Namespace) -> int:
    path = Path(args.path)
    _print({"path": str(path), "exists": path.is_file()}, as_json=args.json)
    return 0 if path.is_file() else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nova", description="Lawful Nova local CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    health = sub.add_parser("health", help="Check local Lawful Nova readiness")
    health.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    health.set_defaults(func=health_command)

    chat = sub.add_parser("chat", help="Ask the local Lawful Nova slice")
    chat.add_argument("prompt", nargs="?", default="observe lawful nova")
    chat.add_argument("--tenant", default="local")
    chat.add_argument("--capability", default="observe")
    chat.add_argument("--json", action="store_true")
    chat.set_defaults(func=ask_command)

    run = sub.add_parser("run", help="Run a one-shot local Lawful Nova prompt")
    run.add_argument("prompt")
    run.add_argument("--tenant", default="local")
    run.add_argument("--capability", default="observe")
    run.add_argument("--json", action="store_true")
    run.set_defaults(func=ask_command)

    serve = sub.add_parser("serve", help="Start the local Lawful Nova /health API")
    serve.set_defaults(func=serve_command)

    plan = sub.add_parser("plan", help="Create a read-only planning task on the operator kernel")
    plan.add_argument("prompt")
    plan.add_argument("--json", action="store_true")
    plan.set_defaults(func=plan_command)

    task = sub.add_parser("task", help="Operator task commands")
    task_sub = task.add_subparsers(dest="task_command", required=True)
    task_list = task_sub.add_parser("list", help="List tasks")
    task_list.add_argument("--json", action="store_true")
    task_list.set_defaults(func=task_list_command)
    task_resume = task_sub.add_parser("resume", help="Send a follow-up message to a task")
    task_resume.add_argument("task_id")
    task_resume.add_argument("message")
    task_resume.add_argument("--json", action="store_true")
    task_resume.set_defaults(func=task_resume_command)

    open_cmd = sub.add_parser("open", help="Verify a workspace file path exists")
    open_cmd.add_argument("path")
    open_cmd.add_argument("--json", action="store_true")
    open_cmd.set_defaults(func=open_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
