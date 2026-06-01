"""Lab Console CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lab.common import DEFAULT_LEDGER_PATH, DEFAULT_RUNTIME_ROOT, json_stable
from lab.experiment import ExperimentError, list_experiments, revert_experiment, show_experiment
from lab.project import ProjectError, init_project, load_manifest, project_status, workspace_path
from lab.session import SessionError, end_session_cli, start_session_cli


def _print(payload: dict, *, output: str) -> None:
    if output == "json":
        print(json_stable(payload, pretty=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


def cmd_init(args: argparse.Namespace) -> int:
    if not args.spec and not args.project:
        print("[lab] init FAILED: provide --project or --spec", file=sys.stderr)
        return 1
    try:
        result = init_project(
            spec_path=args.spec or None,
            project_id=args.project or None,
            source=args.source,
            branch=args.branch or None,
            runtime_root=Path(args.runtime_root) if args.runtime_root else None,
            ledger_path=Path(args.ledger_path) if args.ledger_path else None,
        )
    except ProjectError as exc:
        print(f"[lab] init FAILED: {exc}", file=sys.stderr)
        return 1
    payload = {"mode": "init", **result}
    _print(payload, output=args.output)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    try:
        payload = project_status(
            args.project,
            runtime_root=Path(args.runtime_root) if args.runtime_root else None,
        )
    except ProjectError as exc:
        print(f"[lab] status FAILED: {exc}", file=sys.stderr)
        return 1
    payload["mode"] = "status"
    _print(payload, output=args.output)
    return 0


def cmd_session_start(args: argparse.Namespace) -> int:
    try:
        payload = start_session_cli(
            project_id=args.project,
            agent=args.agent,
            session_id=args.session_id or None,
            runtime_root=Path(args.runtime_root) if args.runtime_root else None,
            ledger_path=Path(args.ledger_path) if args.ledger_path else None,
        )
    except (ProjectError, SessionError) as exc:
        print(f"[lab] session start FAILED: {exc}", file=sys.stderr)
        return 1
    payload["mode"] = "session_start"
    _print(payload, output=args.output)
    return 0


def cmd_session_end(args: argparse.Namespace) -> int:
    try:
        receipt = end_session_cli(
            project_id=args.project,
            session_id=args.session_id,
            status=args.status,
            runtime_root=Path(args.runtime_root) if args.runtime_root else None,
            ledger_path=Path(args.ledger_path) if args.ledger_path else None,
        )
    except (ProjectError, SessionError) as exc:
        print(f"[lab] session end FAILED: {exc}", file=sys.stderr)
        return 1
    payload = {"mode": "session_end", "receipt": receipt}
    _print(payload, output=args.output)
    return 0 if receipt.get("status") == "ok" else 1


def cmd_experiments_list(args: argparse.Namespace) -> int:
    try:
        rows = list_experiments(
            args.project,
            file_filter=args.file or None,
            status_filter=args.status or None,
            runtime_root=Path(args.runtime_root) if args.runtime_root else None,
        )
    except ProjectError as exc:
        print(f"[lab] experiments list FAILED: {exc}", file=sys.stderr)
        return 1
    payload = {"mode": "experiments_list", "experiments": rows}
    _print(payload, output=args.output)
    return 0


def cmd_experiment_show(args: argparse.Namespace) -> int:
    try:
        payload = show_experiment(
            args.project,
            args.exp,
            runtime_root=Path(args.runtime_root) if args.runtime_root else None,
        )
    except ExperimentError as exc:
        print(f"[lab] experiment show FAILED: {exc}", file=sys.stderr)
        return 1
    payload["mode"] = "experiment_show"
    _print(payload, output=args.output)
    return 0


def cmd_experiment_revert(args: argparse.Namespace) -> int:
    try:
        manifest = load_manifest(
            args.project,
            runtime_root=Path(args.runtime_root) if args.runtime_root else None,
        )
        ws = workspace_path(
            args.project,
            runtime_root=Path(args.runtime_root) if args.runtime_root else None,
        )
        payload = revert_experiment(
            args.project,
            args.exp,
            workspace=ws,
            confirm=bool(args.confirm),
        )
    except (ProjectError, ExperimentError) as exc:
        print(f"[lab] experiment revert FAILED: {exc}", file=sys.stderr)
        return 1
    payload["mode"] = "experiment_revert"
    payload["workspace_path"] = str(ws.resolve())
    _print(payload, output=args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lab-Grade Coding Console v1")
    parser.add_argument("--runtime-root", default=str(DEFAULT_RUNTIME_ROOT))
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--output", choices=("json", "text"), default="text")
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="initialize lab project with worktree")
    init_p.add_argument("--project", default="", help="project id (required without --spec)")
    init_p.add_argument("--spec", default="", help="path to lab spec yaml/json")
    init_p.add_argument("--source", default=".", help="source git repo path")
    init_p.add_argument("--branch", default="", help="optional git ref for worktree")
    init_p.set_defaults(func=cmd_init)

    status_p = sub.add_parser("status", help="project manifest and workspace HEAD")
    status_p.add_argument("--project", required=True)
    status_p.set_defaults(func=cmd_status)

    session_p = sub.add_parser("session", help="session lifecycle")
    session_sub = session_p.add_subparsers(dest="session_command", required=True)

    start_p = session_sub.add_parser("start", help="start coding session")
    start_p.add_argument("--project", required=True)
    start_p.add_argument("--agent", required=True)
    start_p.add_argument("--session-id", default="")
    start_p.set_defaults(func=cmd_session_start)

    end_p = session_sub.add_parser("end", help="end coding session and emit receipt")
    end_p.add_argument("--project", required=True)
    end_p.add_argument("--session-id", required=True)
    end_p.add_argument("--status", choices=("ok", "failed"), default="ok")
    end_p.set_defaults(func=cmd_session_end)

    exp_p = sub.add_parser("experiments", help="experiment index")
    exp_sub = exp_p.add_subparsers(dest="experiments_command", required=True)
    list_p = exp_sub.add_parser("list", help="list experiments")
    list_p.add_argument("--project", required=True)
    list_p.add_argument("--file", default="")
    list_p.add_argument("--status", default="")
    list_p.set_defaults(func=cmd_experiments_list)

    show_p = sub.add_parser("experiment", help="single experiment")
    show_sub = show_p.add_subparsers(dest="experiment_command", required=True)
    show_one = show_sub.add_parser("show", help="show experiment metadata")
    show_one.add_argument("--project", required=True)
    show_one.add_argument("--exp", required=True)
    show_one.set_defaults(func=cmd_experiment_show)

    revert_p = show_sub.add_parser("revert", help="revert workspace to clean state")
    revert_p.add_argument("--project", required=True)
    revert_p.add_argument("--exp", required=True)
    revert_p.add_argument("--confirm", action="store_true")
    revert_p.set_defaults(func=cmd_experiment_revert)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
