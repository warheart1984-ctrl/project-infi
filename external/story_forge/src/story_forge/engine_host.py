from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any

from story_forge.engine_adapter import DEFAULT_ENGINE_PROVIDER


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Story Forge external engine host.")
    parser.add_argument(
        "--provider",
        default=DEFAULT_ENGINE_PROVIDER,
        choices=[DEFAULT_ENGINE_PROVIDER],
        help="Engine family proxied by this external engine host.",
    )
    parser.add_argument(
        "--runtime-root",
        default=None,
        help="Optional runtime root directory for the proxied engine.",
    )
    parser.add_argument(
        "--capture-root",
        default=None,
        help="Optional capture root directory for the proxied engine.",
    )
    parser.add_argument(
        "--score-step-base",
        type=int,
        default=6,
        help="Base narrative score delta for each runtime step.",
    )
    parser.add_argument(
        "--engine-command",
        default=None,
        help="Optional command used for the proxied scene archive engine.",
    )
    parser.add_argument(
        "--engine-command-workdir",
        default=None,
        help="Optional working directory for the proxied scene archive engine.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    raw_request = sys.stdin.read()
    command = _resolved_engine_command(args)
    environment = os.environ.copy()
    if args.engine_command is None:
        environment.update(_default_engine_environment())

    try:
        completed = subprocess.run(
            command,
            input=raw_request,
            capture_output=True,
            text=True,
            cwd=args.engine_command_workdir,
            env=environment,
            shell=False,
            check=False,
        )
    except OSError as exc:
        print(json.dumps(_error("BoundaryError", f"Engine host could not launch proxied engine: {exc}")))
        return 0

    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        stdout = (completed.stdout or "").strip()
        detail = stderr or stdout or f"exit code {completed.returncode}"
        print(json.dumps(_error("BoundaryError", f"Proxied engine failed: {detail}")))
        return 0

    raw_stdout = (completed.stdout or "").strip()
    if not raw_stdout:
        print(json.dumps(_error("BoundaryError", "Proxied engine returned no stdout payload.")))
        return 0

    try:
        response = json.loads(raw_stdout)
    except json.JSONDecodeError:
        print(json.dumps(_error("SemanticError", "Proxied engine returned invalid JSON.")))
        return 0

    if not isinstance(response, dict):
        print(json.dumps(_error("SemanticError", "Proxied engine must return a JSON object.")))
        return 0

    print(json.dumps(response))
    return 0


def _resolved_engine_command(args: argparse.Namespace) -> list[str]:
    explicit = _normalized_command(args.engine_command)
    if explicit:
        return explicit

    if getattr(sys, "frozen", False):
        command: list[str] = [sys.executable, "--scene-archive-engine"]
    else:
        command = [sys.executable, "-m", "story_forge.scene_archive_engine"]

    if args.runtime_root is not None:
        command.extend(["--runtime-root", str(args.runtime_root)])
    if args.capture_root is not None:
        command.extend(["--capture-root", str(args.capture_root)])
    if int(args.score_step_base) != 6:
        command.extend(["--score-step-base", str(int(args.score_step_base))])
    return command


def _normalized_command(command: str | list[str] | None) -> list[str]:
    if isinstance(command, list):
        return [str(part).strip() for part in command if str(part).strip()]
    if isinstance(command, str) and command.strip():
        return shlex.split(command, posix=False)
    return []


def _default_engine_environment() -> dict[str, str]:
    if getattr(sys, "frozen", False):
        return {}
    src_root = Path(__file__).resolve().parents[1]
    existing = os.environ.get("PYTHONPATH", "").strip()
    python_path = str(src_root)
    if existing:
        python_path = os.pathsep.join([python_path, existing])
    return {"PYTHONPATH": python_path}


def _error(error_type: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "module": "engine",
        "error_type": error_type,
        "message": message,
        "details": {},
    }


if __name__ == "__main__":
    raise SystemExit(main())
