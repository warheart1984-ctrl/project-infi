#!/usr/bin/env python3
"""Scan source trees for likely unwired UL response paths."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from tools.ul._common import (
    PROJECT_ROOT,
    SCAN_ALLOWLIST_FILES,
    SCAN_ALLOWLIST_SUFFIXES,
    SCAN_SKIP_PARTS,
    UL_WRAP_MARKERS,
    print_json,
    relative_path,
)

RETURN_DICT_RE = re.compile(r"\breturn\s+\{")
DEF_RE = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def _should_skip(path: Path) -> bool:
    if any(part in SCAN_SKIP_PARTS for part in path.parts):
        return True
    if path.name in SCAN_ALLOWLIST_FILES:
        return True
    return path.name.endswith(SCAN_ALLOWLIST_SUFFIXES)


def scan_paths(paths: list[Path], *, min_returns: int = 2) -> dict[str, object]:
    wired: list[str] = []
    candidates: list[dict[str, object]] = []
    scanned_files = 0

    for root in paths:
        if not root.exists():
            continue
        files = [root] if root.is_file() else sorted(root.rglob("*.py"))
        for file_path in files:
            if _should_skip(file_path):
                continue
            scanned_files += 1
            text = file_path.read_text(encoding="utf-8", errors="replace")
            has_wrap = any(marker in text for marker in UL_WRAP_MARKERS)
            return_count = len(RETURN_DICT_RE.findall(text))
            rel = relative_path(file_path)

            if has_wrap:
                wired.append(rel)
                continue

            if return_count < min_returns:
                continue

            functions = DEF_RE.findall(text)
            candidates.append(
                {
                    "file": rel,
                    "return_dict_count": return_count,
                    "function_count": len(functions),
                    "reason": "dict returns without UL wrap markers",
                }
            )

    return {
        "scanned_files": scanned_files,
        "wired_file_count": len(wired),
        "candidate_unwired_count": len(candidates),
        "wired_files": wired,
        "candidate_unwired": sorted(
            candidates,
            key=lambda item: (-int(item["return_dict_count"]), str(item["file"])),
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scan for likely unwired UL response paths.")
    parser.add_argument(
        "--paths",
        nargs="+",
        default=["src"],
        help="Files or directories to scan (default: src).",
    )
    parser.add_argument(
        "--min-returns",
        type=int,
        default=2,
        help="Minimum return-dict occurrences before flagging a file (default: 2).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    roots = [(PROJECT_ROOT / path).resolve() for path in args.paths]
    report = scan_paths(roots, min_returns=max(1, args.min_returns))
    print_json(report)
    return 1 if report["candidate_unwired_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
