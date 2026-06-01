from __future__ import annotations

import os
from pathlib import Path
import stat
import sys


DEFAULT_APP_DIR_NAME = "StoryForge"
DEFAULT_PUBLIC_OUTPUTS_DIR_NAME = "Story Forge Outputs"


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def workspace_root() -> Path:
    root = app_root()
    if getattr(sys, "frozen", False):
        if root.name.lower() == "dist":
            return root.parent.parent
        return root.parent
    return root.parent


def public_outputs_root() -> Path:
    return workspace_root() / DEFAULT_PUBLIC_OUTPUTS_DIR_NAME


def default_movie_output_root() -> Path:
    return public_outputs_root() / "movies"


def user_data_root() -> Path:
    override = os.environ.get("STORY_FORGE_USER_DATA_DIR", "").strip()
    if override:
        return Path(override).resolve()

    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app_data:
        return Path(local_app_data).resolve() / DEFAULT_APP_DIR_NAME

    app_data = os.environ.get("APPDATA", "").strip()
    if app_data:
        return Path(app_data).resolve() / DEFAULT_APP_DIR_NAME

    home = Path.home()
    if os.name != "nt":
        return home / ".local" / "share" / DEFAULT_APP_DIR_NAME
    return app_root() / ".runtime"


def ensure_private_directory(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        try:
            current_mode = stat.S_IMODE(target.stat().st_mode)
            if current_mode != 0o700:
                target.chmod(0o700)
        except OSError:
            pass
    return target
