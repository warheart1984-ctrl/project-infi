#!/usr/bin/env python3
"""Dry-run and send operator SMS pages (immune escalation + dashboard alerts).

Usage:
  python tools/ops/operator_pager_cli.py status
  python tools/ops/operator_pager_cli.py dry-run immune --session sess-1 --response CLAMP
  python tools/ops/operator_pager_cli.py dry-run dashboard
  python tools/ops/operator_pager_cli.py send immune --session sess-1 --response CLAMP
  python tools/ops/operator_pager_cli.py send dashboard --force
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.operator_pager import (  # noqa: E402
    format_dashboard_alert_page,
    format_immune_escalation_page,
    maybe_page_dashboard_alerts,
    maybe_page_immune_escalation,
    pager_config_from_env,
    pager_is_configured,
    should_page_for_dashboard_alert,
    should_page_for_escalation,
)
from src.operator_infinity1_dashboard import _monitoring_summary  # noqa: E402


def _cmd_status(_: argparse.Namespace) -> int:
    cfg = pager_config_from_env()
    print(json.dumps({"configured": pager_is_configured(cfg), "config_keys": sorted(cfg.keys())}, indent=2))
    return 0


def _immune_escalation(args: argparse.Namespace) -> dict:
    return {
        "response": str(args.response or "CLAMP").upper(),
        "allowed": str(args.response or "CLAMP").upper() != "REJECT",
        "reason": args.reason or "cli_dry_run",
    }


def _cmd_dry_run(args: argparse.Namespace) -> int:
    if args.target == "immune":
        escalation = _immune_escalation(args)
        if not should_page_for_escalation(escalation):
            print("Would skip: escalation does not meet paging threshold.")
            return 0
        body = format_immune_escalation_page(args.session, escalation)
        print(body)
        print(f"\nlength={len(body)} configured={pager_is_configured()}")
        return 0

    monitoring = _monitoring_summary()
    alerts = monitoring.get("alerts") or []
    pageable = [a for a in alerts if should_page_for_dashboard_alert(a)]
    if not pageable:
        print("No high/critical dashboard alerts to page.")
        return 0
    for alert in pageable:
        print(format_dashboard_alert_page(alert))
        print("---")
    print(f"count={len(pageable)} configured={pager_is_configured()}")
    return 0


def _cmd_send(args: argparse.Namespace) -> int:
    if args.target == "immune":
        escalation = _immune_escalation(args)
        result = maybe_page_immune_escalation(args.session, escalation)
        print(json.dumps(result or {"skipped": True}, indent=2, default=str))
        return 0 if (result is None or result.get("ok") or result.get("skipped")) else 1

    monitoring = _monitoring_summary()
    alerts = monitoring.get("alerts") or []
    results = maybe_page_dashboard_alerts(alerts, force=bool(args.force))
    print(json.dumps(results, indent=2, default=str))
    return 0 if all(r.get("ok") or r.get("skipped") for r in results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Operator Twilio pager dry-run and send")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="Show pager configuration status")
    status.set_defaults(func=_cmd_status)

    for name in ("dry-run", "send"):
        cmd = sub.add_parser(name, help=f"{name} immune or dashboard pages")
        cmd.add_argument("target", choices=("immune", "dashboard"))
        cmd.add_argument("--session", default="cli-session", help="Session id (immune)")
        cmd.add_argument(
            "--response",
            default="CLAMP",
            choices=("CLAMP", "REROUTE", "REJECT", "ALLOW"),
            help="Immune escalation response (immune)",
        )
        cmd.add_argument("--reason", default="", help="Escalation reason (immune)")
        cmd.add_argument(
            "--force",
            action="store_true",
            help="Re-page dashboard alerts even if fingerprint was already sent",
        )
        cmd.set_defaults(func=_cmd_dry_run if name == "dry-run" else _cmd_send)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
