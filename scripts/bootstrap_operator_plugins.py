#!/usr/bin/env python3
"""Bootstrap operator plugins: safe native enables, MCP manifest, platform marketplace seed.

Usage (from project-infi root):

  # Operator-only dry run (default)
  python scripts/bootstrap_operator_plugins.py --dry-run

  # Apply operator plug enables
  python scripts/bootstrap_operator_plugins.py

  # Also merge Cursor MCP config into governance manifest
  python scripts/bootstrap_operator_plugins.py --mcp-from-cursor

  # Seed curated marketplace listings for an org
  python scripts/bootstrap_operator_plugins.py --platform-org demo-org

  # Full stack
  python scripts/bootstrap_operator_plugins.py --mcp-from-cursor --platform-org demo-org --report-out .runtime/bootstrap_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.operator_plugin_bootstrap import (  # noqa: E402
    bootstrap_operator_plugins,
    default_cursor_mcp_paths,
    repo_root_from,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap operator plugins and marketplace seed.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan only; do not write enabled_plugs.json, MCP manifest, or platform store.",
    )
    parser.add_argument(
        "--no-operator-plugs",
        action="store_true",
        help="Skip auto-enabling safe native_capability plugs.",
    )
    parser.add_argument(
        "--mcp-from-cursor",
        action="store_true",
        help="Merge ~/.cursor/mcp.json (and project .cursor/mcp.json) into governance MCP manifest.",
    )
    parser.add_argument(
        "--cursor-mcp-path",
        action="append",
        default=[],
        metavar="PATH",
        help="Extra Cursor MCP config path (repeatable). Defaults to project + user config.",
    )
    parser.add_argument(
        "--platform-org",
        default="",
        metavar="ORG_ID",
        help="Publish and install curated marketplace listings for this org.",
    )
    parser.add_argument(
        "--skip-gates",
        action="store_true",
        help="Skip library-gate and plug-adapter-gate after apply.",
    )
    parser.add_argument(
        "--runtime-dir",
        default="",
        metavar="PATH",
        help="Override AAIS runtime dir (default: .runtime or AAIS_RUNTIME_DIR).",
    )
    parser.add_argument(
        "--report-out",
        default="",
        metavar="PATH",
        help="Write JSON readiness report to this file.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = repo_root_from(ROOT)

    cursor_paths: list[Path] = [Path(p) for p in args.cursor_mcp_path]
    if args.mcp_from_cursor and not cursor_paths:
        cursor_paths = default_cursor_mcp_paths(repo_root=repo_root)

    runtime_dir = Path(args.runtime_dir) if args.runtime_dir else None

    report = bootstrap_operator_plugins(
        repo_root=repo_root,
        dry_run=args.dry_run,
        enable_operator_plugs=not args.no_operator_plugs,
        generate_mcp_manifest=args.mcp_from_cursor,
        cursor_mcp_paths=cursor_paths if args.mcp_from_cursor else None,
        platform_org=args.platform_org,
        skip_gates=args.skip_gates,
        runtime_dir=runtime_dir,
    )

    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.report_out:
        out = Path(args.report_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")
        print(f"Wrote report: {out}")

    print(payload)

    return 0 if report.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
