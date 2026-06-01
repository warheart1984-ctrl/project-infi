from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

import uvicorn


APP_NAME = "AAIS"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_APP_BASE = "/app"
KNOWN_COMMANDS = {"start", "prepare", "doctor"}


def normalize_app_base(value: str | None) -> str:
    base = str(value or DEFAULT_APP_BASE).strip() or DEFAULT_APP_BASE
    if base == "/":
        return base
    return "/" + base.strip("/")


def discover_project_root(start: Path | None = None) -> Path:
    candidates = [
        Path(start or Path.cwd()),
        Path(__file__).resolve().parent.parent,
        Path.cwd(),
    ]

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if (resolved / "app" / "main.py").exists() and (resolved / "src" / "api.py").exists():
            return resolved

    raise FileNotFoundError("Could not locate the AAIS project root.")


def packaged_static_dir(root: Path) -> Path:
    return root / "app" / "static"


def frontend_source_dir(root: Path) -> Path:
    return root / "frontend"


def frontend_build_dir(root: Path) -> Path:
    return frontend_source_dir(root) / "build"


def has_modern_frontend_bundle(directory: Path) -> bool:
    return (directory / "index.html").exists() and (directory / "assets").is_dir()


def npm_executable() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


def _copy_tree_contents(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)

    for child in list(target.iterdir()):
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    for child in source.iterdir():
        destination = target / child.name
        if child.is_dir():
            shutil.copytree(child, destination)
        else:
            shutil.copy2(child, destination)


def build_frontend_bundle(root: Path, app_base: str) -> Path:
    frontend_dir = frontend_source_dir(root)
    if not (frontend_dir / "package.json").exists():
        raise FileNotFoundError("frontend/package.json is missing.")
    if not (frontend_dir / "node_modules").exists():
        raise FileNotFoundError(
            "frontend/node_modules is missing. Run npm install in frontend before building the AAIS app bundle."
        )

    env = os.environ.copy()
    normalized_base = normalize_app_base(app_base)
    env["VITE_ROUTER_BASENAME"] = normalized_base
    env["VITE_APP_BASE"] = normalized_base
    env["AAIS_APP_BASE"] = normalized_base

    subprocess.run(
        [npm_executable(), "run", "build"],
        cwd=str(frontend_dir),
        env=env,
        check=True,
    )
    return frontend_build_dir(root)


def prepare_frontend_bundle(root: Path, app_base: str, *, force_build: bool = False) -> Path:
    target = packaged_static_dir(root)
    if has_modern_frontend_bundle(target) and not force_build:
        return target

    source_bundle = frontend_build_dir(root)
    if force_build or not has_modern_frontend_bundle(source_bundle):
        source_bundle = build_frontend_bundle(root, app_base)

    if not has_modern_frontend_bundle(source_bundle):
        raise FileNotFoundError(
            "AAIS frontend build output is missing. Expected frontend/build with index.html and assets/."
        )

    _copy_tree_contents(source_bundle, target)
    return target


def default_user_data_dir() -> Path:
    if sys.platform == "win32":
        base_dir = os.getenv("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base_dir) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path(os.getenv("XDG_DATA_HOME") or (Path.home() / ".local" / "share")) / APP_NAME


def resolve_data_dir(explicit_data_dir: str | None) -> Path:
    selected_data_dir = explicit_data_dir or os.getenv("JARVIS_DATA_DIR")
    if selected_data_dir:
        path = Path(selected_data_dir).expanduser().resolve()
    else:
        path = default_user_data_dir().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def configure_runtime_environment(*, data_dir: Path, static_dir: Path, app_base: str) -> None:
    os.environ["JARVIS_DATA_DIR"] = str(data_dir)
    os.environ["JARVIS_STATIC_DIR"] = str(static_dir)
    os.environ["AAIS_APP_BASE"] = normalize_app_base(app_base)


def wait_for_http(url: str, timeout_seconds: int = 45) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if 200 <= response.status < 500:
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False


def launch_browser_when_ready(url: str, health_url: str) -> None:
    def _open() -> None:
        if wait_for_http(health_url):
            webbrowser.open(url)

    threading.Thread(target=_open, daemon=True).start()


def browser_host(host: str) -> str:
    normalized_host = str(host or "").strip()
    if normalized_host in {"0.0.0.0", "::"}:
        return "127.0.0.1"
    return normalized_host or DEFAULT_HOST


def runtime_summary(root: Path, data_dir: Path, app_base: str) -> dict[str, object]:
    static_dir = packaged_static_dir(root)
    return {
        "app_name": APP_NAME,
        "project_root": str(root),
        "data_dir": str(data_dir),
        "app_base": normalize_app_base(app_base),
        "packaged_static_dir": str(static_dir),
        "packaged_frontend_ready": has_modern_frontend_bundle(static_dir),
        "frontend_source_dir": str(frontend_source_dir(root)),
        "frontend_build_dir": str(frontend_build_dir(root)),
        "frontend_build_ready": has_modern_frontend_bundle(frontend_build_dir(root)),
    }


def handle_prepare(args: argparse.Namespace) -> int:
    root = discover_project_root()
    static_dir = prepare_frontend_bundle(root, args.app_base, force_build=args.force_build)
    summary = runtime_summary(root, resolve_data_dir(args.data_dir), args.app_base)
    summary["prepared_static_dir"] = str(static_dir)
    print(json.dumps(summary, indent=2))
    return 0


def handle_doctor(args: argparse.Namespace) -> int:
    root = discover_project_root()
    summary = runtime_summary(root, resolve_data_dir(args.data_dir), args.app_base)
    print(json.dumps(summary, indent=2))
    return 0


def handle_start(args: argparse.Namespace) -> int:
    root = discover_project_root()
    static_dir = prepare_frontend_bundle(root, args.app_base, force_build=args.force_build)
    data_dir = resolve_data_dir(args.data_dir)
    configure_runtime_environment(data_dir=data_dir, static_dir=static_dir, app_base=args.app_base)

    from src.main import apply_runtime_preset

    apply_runtime_preset(args.preset)

    target_host = browser_host(args.host)
    app_base = normalize_app_base(args.app_base)
    app_url = f"http://{target_host}:{args.port}{app_base}"
    health_url = f"http://{target_host}:{args.port}/health"

    if not args.no_browser:
        launch_browser_when_ready(app_url, health_url)

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cross-platform launcher for the AAIS application shell.")
    subparsers = parser.add_subparsers(dest="command")

    def add_common_arguments(command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument("--app-base", default=DEFAULT_APP_BASE, help="Browser route prefix for the packaged AAIS app.")
        command_parser.add_argument("--data-dir", default=None, help="Optional override for AAIS runtime data storage.")

    start_parser = subparsers.add_parser("start", help="Prepare the UI bundle and launch the AAIS app.")
    add_common_arguments(start_parser)
    start_parser.add_argument("--host", default=DEFAULT_HOST, help="Server host to bind.")
    start_parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port to bind.")
    start_parser.add_argument("--preset", choices=["default", "laptop", "mock"], default="default", help="AAIS runtime preset.")
    start_parser.add_argument("--reload", action="store_true", help="Run uvicorn with live reload for local development.")
    start_parser.add_argument("--force-build", action="store_true", help="Rebuild the frontend bundle before launch.")
    start_parser.add_argument("--no-browser", action="store_true", help="Do not open a browser after the server becomes healthy.")
    start_parser.add_argument("--log-level", default="info", help="uvicorn log level.")
    start_parser.set_defaults(handler=handle_start)

    prepare_parser = subparsers.add_parser("prepare", help="Build and stage the packaged frontend bundle.")
    add_common_arguments(prepare_parser)
    prepare_parser.add_argument("--force-build", action="store_true", help="Rebuild the frontend bundle before staging it.")
    prepare_parser.set_defaults(handler=handle_prepare)

    doctor_parser = subparsers.add_parser("doctor", help="Print cross-platform AAIS runtime diagnostics.")
    add_common_arguments(doctor_parser)
    doctor_parser.set_defaults(handler=handle_doctor)

    return parser


def normalize_argv(argv: list[str] | None) -> list[str]:
    normalized = list(argv if argv is not None else sys.argv[1:])
    if not normalized:
        return ["start"]
    if normalized[0] in {"-h", "--help"}:
        return normalized
    if normalized[0] not in KNOWN_COMMANDS and not normalized[0].startswith("-"):
        return ["start", *normalized]
    if normalized[0].startswith("-"):
        return ["start", *normalized]
    return normalized


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(normalize_argv(argv))
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1
    return int(handler(args) or 0)
