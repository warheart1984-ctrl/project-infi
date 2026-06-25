#!/usr/bin/env python3
"""Disable all unlawful AI agent plugs and emit a shutdown report.

Unlawful plug classes (AAIS governance):
  - cursor_skill  (ungoverned Cursor skill agents)
  - hf_agent_skill (ungoverned Hugging Face agent skills)
  - mcp           (external MCP agent bridges without lawful admission)

Lawful paths (not disabled by this script):
  - native_capability plugs (operator-governed substrate)
  - workflow plugs (catalog-only unless explicitly disabled via --all-non-native)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.plug_adapter_runtime import PlugAdapterRuntime  # noqa: E402
from src.plug_discovery import discover_plugs  # noqa: E402

UNLAWFUL_PLUG_CLASSES = frozenset({"cursor_skill", "hf_agent_skill", "mcp"})
UNLAWFUL_PLUG_ID_PREFIXES = ("mcp.", "skill.", "hf_skill.")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def disable_unlawful_agents(
    *,
    repo_root: Path,
    runtime_dir: Path | None = None,
    disable_workflows: bool = False,
    dry_run: bool = False,
) -> dict:
    runtime = PlugAdapterRuntime(runtime_dir=runtime_dir, repo_root=repo_root)
    plugs = discover_plugs(repo_root=repo_root)

    disabled: list[str] = []
    skipped_lawful: list[str] = []
    already_off: list[str] = []

    enabled_state = runtime._load_enabled()  # noqa: SLF001 — intentional shutdown tool

    for plug in plugs:
        plug_id = str(plug.get("plug_id") or "")
        plug_class = str(plug.get("plug_class") or "")
        if not plug_id:
            continue

        unlawful = (
            plug_class in UNLAWFUL_PLUG_CLASSES
            or any(plug_id.startswith(prefix) for prefix in UNLAWFUL_PLUG_ID_PREFIXES)
        )
        non_native = plug_class not in {"native_capability"}
        should_disable = unlawful or (disable_workflows and non_native)

        if not should_disable:
            skipped_lawful.append(plug_id)
            continue

        if not enabled_state.get(plug_id, False):
            already_off.append(plug_id)
            if not dry_run:
                runtime.set_plug_enabled(plug_id, False)
            continue

        if not dry_run:
            runtime.set_plug_enabled(plug_id, False)
        disabled.append(plug_id)

    report = {
        "shutdown_version": "disable_unlawful_agents.v1",
        "completed_at": _utc_now_iso(),
        "dry_run": dry_run,
        "repo_root": str(repo_root),
        "unlawful_classes": sorted(UNLAWFUL_PLUG_CLASSES),
        "disabled_now": sorted(disabled),
        "already_off": sorted(already_off),
        "left_enabled_lawful": sorted(skipped_lawful),
        "totals": {
            "plugs_scanned": len(plugs),
            "disabled_now": len(disabled),
            "already_off": len(already_off),
            "lawful_unchanged": len(skipped_lawful),
        },
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Disable unlawful AI agent plugs.")
    parser.add_argument("--dry-run", action="store_true", help="Report only; do not write state.")
    parser.add_argument(
        "--disable-workflows",
        action="store_true",
        help="Also disable workflow plugs (non-native). Default: only unlawful classes.",
    )
    parser.add_argument("--runtime-dir", default="", metavar="PATH")
    parser.add_argument("--report-out", default="", metavar="PATH")
    args = parser.parse_args()

    runtime_dir = Path(args.runtime_dir).expanduser() if args.runtime_dir else None
    report = disable_unlawful_agents(
        repo_root=ROOT,
        runtime_dir=runtime_dir,
        disable_workflows=args.disable_workflows,
        dry_run=args.dry_run,
    )

    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(payload)

    if args.report_out:
        out = Path(args.report_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
