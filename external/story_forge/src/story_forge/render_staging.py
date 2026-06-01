from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import time

from story_forge.app_paths import ensure_private_directory, user_data_root
from story_forge.identity import PACKAGE_VERSION


MOVIE_STAGING_SCHEMA = "story_forge_movie_staging/v1"
MOVIE_STAGING_PREFIX = "render_"
MOVIE_STAGING_META_FILENAME = "meta.json"
MOVIE_STAGING_TTL_SECONDS = 48 * 3600


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_movie_staging_root() -> Path:
    return user_data_root() / "staging" / "movie"


def prepare_movie_staging_root(path: str | Path | None = None) -> Path:
    target = Path(path) if path is not None else default_movie_staging_root()
    return ensure_private_directory(target)


def write_movie_staging_metadata(
    staging_dir: str | Path,
    *,
    render_id: str,
) -> Path:
    target = Path(staging_dir) / MOVIE_STAGING_META_FILENAME
    payload = {
        "schema": MOVIE_STAGING_SCHEMA,
        "created_at": _now_iso(),
        "pid": os.getpid(),
        "version": PACKAGE_VERSION,
        "render_id": render_id,
    }
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target


def run_movie_staging_janitor(
    staging_root: str | Path | None = None,
    *,
    ttl_seconds: int = MOVIE_STAGING_TTL_SECONDS,
) -> int:
    root = Path(staging_root) if staging_root is not None else default_movie_staging_root()
    if not root.exists():
        return 0

    now = time.time()
    removed = 0
    for candidate in root.glob(f"{MOVIE_STAGING_PREFIX}*"):
        if not candidate.is_dir():
            continue
        try:
            age_seconds = now - candidate.stat().st_mtime
        except OSError:
            continue
        if age_seconds <= ttl_seconds:
            continue
        try:
            shutil.rmtree(candidate, ignore_errors=True)
        except OSError:
            continue
        removed += 1
    return removed
