#!/usr/bin/env python3
"""Probe one payload through AAIS-UL adapters and substrate wrapping."""

from __future__ import annotations

import argparse
import json
from typing import Any

from tools.ul._common import ensure_project_root, load_json_payload, print_json


def probe_payload(raw: Any, *, wrap: bool = False, list_adapters: bool = False) -> dict[str, Any]:
    ensure_project_root()
    from src.aais_ul import DEFAULT_REGISTRY, adapt_ingress, build_ul_snapshot
    from src.aais_ul_substrate import attach_ul_substrate, substrate_status

    matched: list[dict[str, Any]] = []
    for adapter in DEFAULT_REGISTRY.adapters:
        if adapter.supports(raw):
            payload = adapter.adapt(raw).to_dict()
            matched.append(
                {
                    "adapter": adapter.name,
                    "section": payload.get("section"),
                    "kind": payload.get("kind"),
                    "source": payload.get("source"),
                }
            )
            if not list_adapters:
                break

    result: dict[str, Any] = {
        "input_type": type(raw).__name__,
        "matched_adapters": matched,
        "primary_adapter": matched[0]["adapter"] if matched else None,
        "primary_section": matched[0]["section"] if matched else None,
    }

    if matched and not list_adapters:
        result["payload"] = adapt_ingress(raw, required=False) or {}
    elif not matched:
        try:
            result["payload"] = adapt_ingress(raw)
        except ValueError as exc:
            result["adapt_error"] = str(exc)

    snapshot = build_ul_snapshot(ingress=[raw] if isinstance(raw, dict) else None)
    result["ul_trace"] = snapshot

    if wrap and isinstance(raw, dict):
        wrapped = attach_ul_substrate(raw)
        result["wrapped"] = {
            "has_ul_substrate": bool(wrapped.get("ul_substrate")),
            "ul_trace_count": (wrapped.get("ul_trace") or {}).get("count", 0),
            "sections": (wrapped.get("ul_trace") or {}).get("sections", []),
        }

    if list_adapters:
        result["registry"] = substrate_status()

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe one payload through AAIS-UL adapters.")
    parser.add_argument("--file", help="JSON file containing the payload to probe.")
    parser.add_argument("--json", help="Inline JSON payload.")
    parser.add_argument(
        "--wrap",
        action="store_true",
        help="Also run attach_ul_substrate and report wrapped trace.",
    )
    parser.add_argument(
        "--list-adapters",
        action="store_true",
        help="Include full adapter registry in output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        payload = load_json_payload(file_path=args.file, inline=args.json)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"ul probe: invalid input: {exc}")
        return 2

    report = probe_payload(payload, wrap=args.wrap, list_adapters=args.list_adapters)
    print_json(report)
    return 0 if report.get("primary_adapter") else 1


if __name__ == "__main__":
    raise SystemExit(main())
