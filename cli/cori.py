#!/usr/bin/env python3
"""CORI operator CLI — governed constitutional mission entrypoint."""

from __future__ import annotations

import argparse
import json
import os
import sys

import requests

DEFAULT_AAIS_URL = os.environ.get("AAIS_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
DEFAULT_DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "http://127.0.0.1:8100").rstrip("/")
GOVERNED_MISSION_URL = f"{DEFAULT_AAIS_URL}/governed/mission"


def _mission_command(text: str, *, operator_id: str | None, session_id: str | None, json_out: bool) -> int:
    payload: dict[str, str] = {"text": text}
    if operator_id:
        payload["operator_id"] = operator_id
    if session_id:
        payload["session_id"] = session_id

    try:
        response = requests.post(GOVERNED_MISSION_URL, json=payload, timeout=120)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"cori: governed mission failed: {exc}", file=sys.stderr)
        return 1

    trace = response.json()
    if json_out:
        print(json.dumps(trace, indent=2, sort_keys=True))
        return 0

    law_eval = trace.get("law_eval") or {}
    urg = trace.get("urg_receipt") or {}
    aaes = trace.get("aaes_receipt") or {}
    nexus = trace.get("nexus_event") or {}

    print("\n=== CORI GOVERNED MISSION TRACE ===")
    print(f"Status:         {trace.get('status', 'unknown')}")
    print(f"LAW_EVAL:       {law_eval.get('id', '—')}")
    print(f"URG Mission:    {urg.get('mission_id', '—')}")
    print(f"AAES Exec:      {aaes.get('execution_id') or aaes.get('trace_id', '—')}")
    print(f"Nexus Event:    {nexus.get('event_id') or nexus.get('recorded_at', '—')}")
    print("====================================\n")
    return 0


def _trace_command(mission_id: str) -> int:
    url = f"{DEFAULT_DASHBOARD_URL}/dashboard/trace/{mission_id}"
    try:
        response = requests.get(url, timeout=60)
    except requests.RequestException as exc:
        print(f"cori: trace fetch failed: {exc}", file=sys.stderr)
        return 1

    if response.status_code == 404:
        print(f"Mission trace not found: {mission_id}", file=sys.stderr)
        return 1
    try:
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"cori: trace fetch failed: {exc}", file=sys.stderr)
        return 1

    data = response.json()
    print(f"\nMission: {data.get('mission_id')}\n")
    for event in data.get("trace", []):
        print(f"[{event.get('time')}] {event.get('event_type')}")
        print(json.dumps(event.get("payload"), indent=2))
        print("-" * 60)
    print("\nEnd of trace.\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cori", description="CORI Operator CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    mission_parser = subparsers.add_parser(
        "mission",
        help="Submit a governed mission through the full constitutional spine",
    )
    mission_parser.add_argument("text", help="Operator turn text for Lawful Nova evaluation")
    mission_parser.add_argument("--operator-id", default=None, help="Steward / operator id")
    mission_parser.add_argument("--session-id", default=None, help="Optional AAIS session id")
    mission_parser.add_argument("--json", action="store_true", help="Emit full JSON trace")

    trace_parser = subparsers.add_parser(
        "trace",
        help="Fetch and pretty-print the constitutional trace for a mission",
    )
    trace_parser.add_argument("mission_id", help="URG mission id from a governed mission trace")

    args = parser.parse_args(argv)
    if args.command == "mission":
        return _mission_command(
            args.text,
            operator_id=args.operator_id,
            session_id=args.session_id,
            json_out=args.json,
        )
    if args.command == "trace":
        return _trace_command(args.mission_id)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
