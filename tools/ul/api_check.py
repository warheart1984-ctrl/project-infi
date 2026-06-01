#!/usr/bin/env python3
"""Optional live API checks for AAIS-UL substrate endpoints."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request

from tools.ul._common import print_json


def check_api(base_url: str, *, timeout: float = 5.0) -> dict[str, object]:
    base = base_url.rstrip("/")
    url = f"{base}/api/jarvis/ul-substrate/status"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "url": url,
            "error": str(exc),
            "reason": "API unreachable; start Jarvis before running api-check.",
        }

    substrate = body.get("ul_substrate") or {}
    adapter_count = int(substrate.get("adapter_count") or 0)
    ok = adapter_count >= 10 and bool(substrate.get("contract_version"))
    return {
        "ok": ok,
        "url": url,
        "adapter_count": adapter_count,
        "contract_version": substrate.get("contract_version"),
        "substrate_id": substrate.get("substrate_id"),
        "response": body,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check live AAIS-UL substrate API status.")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:5000",
        help="Jarvis API base URL (default: http://127.0.0.1:5000).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="HTTP timeout in seconds.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = check_api(args.base_url, timeout=args.timeout)
    print_json(report)
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
