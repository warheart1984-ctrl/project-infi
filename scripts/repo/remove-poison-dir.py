#!/usr/bin/env python3
"""Remove whitespace-only poison directories at repo root (Windows-safe)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def remove_poison_dirs(repo_root: Path) -> list[str]:
    removed: list[str] = []
    for entry in os.scandir(repo_root):
        if not entry.is_dir():
            continue
        if entry.name.strip():
            continue
        long_path = "\\\\?\\" + os.path.abspath(entry.path)
        dest = "\\\\?\\" + os.path.abspath(repo_root / "_poison_dir_delete_me")
        try:
            os.rename(long_path, dest)
            os.rmdir(dest)
            removed.append(repr(entry.name))
        except OSError as exc:
            raise SystemExit(f"failed to remove poison dir {entry.path!r}: {exc}") from exc
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove whitespace-only root poison directories.")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    removed = remove_poison_dirs(repo_root)
    if removed:
        print(f"removed {len(removed)} poison dir(s): {', '.join(removed)}")
    else:
        print("no poison dirs found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
