#!/usr/bin/env python3
"""Desktop window entrypoint — local pywebview shell around AAIS."""

from __future__ import annotations

import os
import sys
import threading
import time
import urllib.request
from pathlib import Path


def _resolve_project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _load_dotenv(root: Path) -> None:
    env_path = root / ".env"
    if not env_path.is_file():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path, override=False)
    except ImportError:
        pass


def _default_data_dir(root: Path) -> Path:
    data = root / ".runtime" / "aais-data"
    data.mkdir(parents=True, exist_ok=True)
    return data


def _wait_for_health(url: str, timeout_seconds: int = 60) -> bool:
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


def _start_server(root: Path, data_dir: str, host: str, port: int) -> None:
    os.chdir(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from aais.launcher import (
        configure_runtime_environment,
        discover_project_root,
        prepare_frontend_bundle,
        resolve_data_dir,
    )
    from src.main import apply_runtime_preset

    project_root = discover_project_root(root)
    static_dir = prepare_frontend_bundle(project_root, "/app", force_build=False)
    resolved_data = resolve_data_dir(data_dir)
    configure_runtime_environment(data_dir=resolved_data, static_dir=static_dir, app_base="/app")
    apply_runtime_preset(os.getenv("AAIS_PRESET", "default"))

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level="info",
    )


def main() -> int:
    root = _resolve_project_root()
    _load_dotenv(root)

    data_dir = os.getenv("JARVIS_DATA_DIR") or str(_default_data_dir(root))
    host = os.getenv("AAIS_HOST", "127.0.0.1")
    port = int(os.getenv("AAIS_PORT", "8000"))
    app_url = f"http://{host}:{port}/app"
    health_url = f"http://{host}:{port}/health"

    server_thread = threading.Thread(
        target=_start_server,
        args=(root, data_dir, host, port),
        daemon=True,
        name="aais-desktop-server",
    )
    server_thread.start()

    if not _wait_for_health(health_url):
        print(f"AAIS did not become healthy at {health_url}", file=sys.stderr)
        return 1

    try:
        import webview
    except ImportError as exc:
        print(
            "pywebview is required for the desktop window. "
            'Install with: pip install -e ".[desktop]"',
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    webview.create_window("AAIS", app_url, width=1280, height=800)
    webview.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
