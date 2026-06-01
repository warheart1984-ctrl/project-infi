#!/usr/bin/env python3
"""Normalize shell scripts to LF line endings (Windows checkout safe)."""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: fix-sh-lf.py FILE...", file=sys.stderr)
        return 2
    for arg in sys.argv[1:]:
        path = Path(arg)
        data = path.read_bytes()
        text = data.decode("utf-8")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        path.write_bytes(text.encode("utf-8"))
        print(f"normalized: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
