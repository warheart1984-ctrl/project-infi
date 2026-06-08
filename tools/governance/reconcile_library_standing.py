"""Batch reconcile Library Standing for manifest documents and store contributions."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_PROMOTE = REPO_ROOT / "tools" / "governance" / "promote_discovery_documents.py"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Preview reconcile only")
    parser.add_argument("--no-auto-promote", action="store_true", help="Disable pattern policy")
    args = parser.parse_args()

    cmd = [sys.executable, str(_PROMOTE)]
    if args.dry_run:
        cmd.append("--dry-run")
    if args.no_auto_promote:
        cmd.append("--no-auto-promote")
    return subprocess.call(cmd, cwd=str(REPO_ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
