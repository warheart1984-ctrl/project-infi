#!/usr/bin/env python3
"""Compare AAIS-UL doctrine sections against live adapter coverage."""

from __future__ import annotations

import argparse
import json

from tools.ul._common import PROJECT_ROOT, ensure_project_root, print_json
from tools.ul.smoke import SMOKE_SAMPLES, _load_sample


def collect_adapter_sections() -> dict[str, object]:
    ensure_project_root()
    from src.aais_ul import DEFAULT_REGISTRY
    from src.aais_ul.runtime import substrate_status

    doctrine_path = PROJECT_ROOT / "src" / "aais_ul.json"
    doctrine = json.loads(doctrine_path.read_text(encoding="utf-8"))
    doctrine_sections = list(doctrine.get("sections") or [])

    section_adapters: dict[str, list[str]] = {}
    for sample in SMOKE_SAMPLES:
        payload = _load_sample(sample)
        for adapter in DEFAULT_REGISTRY.adapters:
            if adapter.supports(payload):
                section = adapter.adapt(payload).section
                section_adapters.setdefault(section, [])
                if adapter.name not in section_adapters[section]:
                    section_adapters[section].append(adapter.name)
                break

    emitted_sections = sorted(section_adapters)
    missing_from_adapters = sorted(set(doctrine_sections) - set(emitted_sections))
    extra_sections = sorted(set(emitted_sections) - set(doctrine_sections))
    status = substrate_status()

    return {
        "doctrine_version": doctrine.get("version"),
        "doctrine_sections": doctrine_sections,
        "adapter_count": len(DEFAULT_REGISTRY.adapters),
        "adapters": status.get("adapters"),
        "sections_with_adapters": section_adapters,
        "emitted_sections_from_smoke": emitted_sections,
        "missing_from_adapters": missing_from_adapters,
        "extra_sections": extra_sections,
        "note": (
            "missing_from_adapters uses smoke-sample coverage only; "
            "sections may still be emitted by adapters not represented in smoke fixtures."
        ),
    }


def collect_lineage_lane_report() -> dict[str, object]:
    ensure_project_root()
    from src.ul_lineage import REQUIRED_NODE_TYPES, SCHEMA_PATH

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    node_enum = (
        schema.get("$defs", {})
        .get("lineage_node", {})
        .get("properties", {})
        .get("node_type", {})
        .get("enum", [])
    )
    missing = sorted(REQUIRED_NODE_TYPES - set(node_enum))
    extra = sorted(set(node_enum) - REQUIRED_NODE_TYPES)
    return {
        "lane": "lineage",
        "schema_path": str(SCHEMA_PATH),
        "required_node_types": sorted(REQUIRED_NODE_TYPES),
        "schema_node_types": node_enum,
        "missing_from_schema": missing,
        "extra_in_schema": extra,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report AAIS-UL doctrine vs adapter drift.")
    parser.add_argument(
        "--lane",
        choices=["lineage"],
        help="Report drift for an extended UL lane (lineage graph node coverage).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.lane == "lineage":
        report = collect_lineage_lane_report()
        print_json(report)
        return 1 if report.get("missing_from_schema") else 0
    report = collect_adapter_sections()
    print_json(report)
    return 1 if report.get("missing_from_adapters") else 0


if __name__ == "__main__":
    raise SystemExit(main())
