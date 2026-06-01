#!/usr/bin/env python3
"""Print Forge platform dashboard: substrates, backends, adapters, gate/lineage status."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path.cwd()
FORGE = REPO_ROOT / "wolf-cog-os" / "forge"
ARTIFACTS = REPO_ROOT / "ci-artifacts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Forge platform dashboard.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run live validators for gate/lineage status (slower).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text dashboard.",
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode, output.splitlines()[-1] if output else ""


def _status_color(level: str, use_color: bool) -> str:
    if not use_color:
        return level.upper()
    colors = {
        "green": "\033[32m",
        "yellow": "\033[33m",
        "red": "\033[31m",
        "reset": "\033[0m",
    }
    return f"{colors.get(level, '')}{level.upper()}{colors['reset']}"


def _level_from_code(code: int, *, warn_on_nonzero: bool = False) -> str:
    if code == 0:
        return "green"
    if warn_on_nonzero:
        return "yellow"
    return "red"


def _substrate_section() -> dict:
    registry = _load_json(FORGE / "substrates" / "registry.json")
    classes = registry.get("substrate_classes", {})
    substrates = registry.get("substrates", {})
    by_class: dict[str, list[str]] = {}
    for sid, spec in substrates.items():
        cls = str(spec.get("class", "unknown"))
        by_class.setdefault(cls, []).append(sid)
    return {
        "registry_version": registry.get("registry_version", "unknown"),
        "class_count": len(classes),
        "substrate_count": len(substrates),
        "classes": [
            {
                "id": cid,
                "tier": spec.get("tier", ""),
                "description": spec.get("description", ""),
                "substrates": sorted(by_class.get(cid, [])),
            }
            for cid, spec in sorted(classes.items())
        ],
        "substrate_ids": sorted(substrates.keys()),
    }


def _backend_section() -> dict:
    registry = _load_json(FORGE / "backends" / "registry.json")
    backends = registry.get("backends", {})
    rows = []
    for bid, spec in sorted(backends.items()):
        rows.append(
            {
                "id": bid,
                "status": spec.get("implementation_status", "unknown"),
                "package_manager": spec.get("package_manager", ""),
                "supported_arches": spec.get("supported_arches", []),
            }
        )
    return {
        "registry_version": registry.get("registry_version", "unknown"),
        "default_backend_id": registry.get("default_backend_id", ""),
        "backends": rows,
    }


def _adapter_section() -> dict:
    registry = _load_json(FORGE / "replay-adapters" / "registry.json")
    substrate_registry = _load_json(FORGE / "substrates" / "registry.json")
    referenced = sorted(
        {
            str(spec.get("replay_adapter", ""))
            for spec in substrate_registry.get("substrates", {}).values()
            if spec.get("replay_adapter")
        }
    )
    adapters = registry.get("adapters", {})
    rows = []
    seen: set[str] = set()
    for adapter_id in referenced:
        spec = adapters.get(adapter_id, {})
        wired = bool(spec.get("wired_in_build"))
        status = spec.get("status", "unknown")
        enabled = wired and status == "production"
        rows.append(
            {
                "id": adapter_id,
                "status": status,
                "wired_in_build": wired,
                "enabled": enabled,
                "registered": adapter_id in adapters,
            }
        )
        seen.add(adapter_id)
    for adapter_id, spec in sorted(adapters.items()):
        if adapter_id in seen:
            continue
        rows.append(
            {
                "id": adapter_id,
                "status": spec.get("status", "unknown"),
                "wired_in_build": bool(spec.get("wired_in_build")),
                "enabled": bool(spec.get("wired_in_build")) and spec.get("status") == "production",
                "registered": True,
            }
        )
    return {
        "registry_version": registry.get("registry_version", "unknown"),
        "default_adapter": registry.get("default_adapter", ""),
        "adapters": rows,
    }


def _lineage_status(live: bool) -> dict:
    lineage_path = ARTIFACTS / "forge-lineage.json"
    nightly_path = ARTIFACTS / "nightly-forge-lineage.json"
    path = lineage_path if lineage_path.is_file() else nightly_path
    if not path.is_file():
        return {"name": "forge-lineage", "level": "yellow", "detail": "no lineage artifact (emit-forge-lineage.py)"}
    if live:
        code, tail = _run(
            [
                sys.executable,
                "wolf-cog-os/scripts/validate-forge-lineage.py",
                "--lineage",
                str(path.relative_to(REPO_ROOT)),
                "--mode",
                "fail",
            ]
        )
        level = _level_from_code(code)
        detail = "valid" if code == 0 else (tail or "validation failed")
    else:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            lineage_id = str(payload.get("lineage_id", ""))[:16]
            level = "green" if lineage_id else "yellow"
            detail = f"{path.name} id={lineage_id}..." if lineage_id else "artifact present but lineage_id missing"
        except json.JSONDecodeError:
            level = "red"
            detail = "invalid JSON"
    return {"name": "forge-lineage", "level": level, "detail": detail, "path": str(path.relative_to(REPO_ROOT))}


def _gate_status(live: bool) -> list[dict]:
    rows: list[dict] = []
    report_path = ARTIFACTS / "forge-platform-gate-report.json"
    shippable_path = ARTIFACTS / "forge-shippable-gate-report.json"
    path = report_path if report_path.is_file() else shippable_path
    label = "platform-gate" if report_path.is_file() else "shippable-gate"
    if path.is_file() and not live:
        report = _load_json(path)
        status = str(report.get("status", "unknown"))
        level = "green" if status == "pass" else ("yellow" if status == "pending" else "red")
        rows.append(
            {
                "name": label,
                "level": level,
                "detail": f"cached report status={status}",
            }
        )
    elif live and label == "platform-gate":
        code, tail = _run([sys.executable, ".github/scripts/check-forge-platform-gate.py", "--mode", "fail"])
        rows.append(
            {
                "name": "platform-gate",
                "level": _level_from_code(code),
                "detail": tail or ("pass" if code == 0 else "failed"),
            }
        )
    elif live:
        code, tail = _run([sys.executable, ".github/scripts/check-forge-shippable-gate.py", "--mode", "fail"])
        rows.append(
            {
                "name": "shippable-gate",
                "level": _level_from_code(code),
                "detail": tail or ("pass" if code == 0 else "failed"),
            }
        )
    else:
        rows.append(
            {
                "name": "platform-gate",
                "level": "yellow",
                "detail": "no cached report (make forge-platform-gate or --check)",
            }
        )

    checks = [
        ("substrate-evolution", ".github/scripts/validate-substrate-evolution-ledger.py"),
        ("backend-evolution", ".github/scripts/validate-backend-evolution-ledger.py"),
        ("pipeline-v2", "wolf-cog-os/scripts/validate-pipeline.py", ["--all"]),
    ]
    for item in checks:
        name = item[0]
        script = item[1]
        extra = list(item[2]) if len(item) > 2 else []
        script_path = REPO_ROOT / script
        if not script_path.is_file():
            rows.append({"name": name, "level": "yellow", "detail": f"missing validator {script}"})
            continue
        if live:
            code, tail = _run([sys.executable, script, *extra, "--mode", "fail"])
            rows.append({"name": name, "level": _level_from_code(code), "detail": tail or ("pass" if code == 0 else "failed")})
        else:
            rows.append({"name": name, "level": "yellow", "detail": "not checked (use --check)"})

    rows.append(_lineage_status(live))
    return rows


def build_dashboard(live: bool) -> dict:
    return {
        "schema_version": "forge-platform-dashboard.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "substrates": _substrate_section(),
        "backends": _backend_section(),
        "replay_adapters": _adapter_section(),
        "gates": _gate_status(live),
    }


def render_text(dashboard: dict, use_color: bool) -> str:
    lines: list[str] = []
    lines.append("Forge Platform Dashboard")
    lines.append("=" * 24)
    lines.append("")

    sub = dashboard["substrates"]
    lines.append(f"Substrate classes ({sub['class_count']})  registry={sub['registry_version']}")
    for row in sub["classes"]:
        ids = ", ".join(row["substrates"]) or "-"
        lines.append(f"  {row['id']:<22} {row.get('tier',''):<10} [{ids}]")
    lines.append("")
    lines.append(f"Substrate ids ({sub['substrate_count']}): {', '.join(sub['substrate_ids'])}")
    lines.append("")

    back = dashboard["backends"]
    lines.append(f"Rootfs backends ({len(back['backends'])})  default={back['default_backend_id']}")
    for row in back["backends"]:
        arches = ",".join(row["supported_arches"])
        lines.append(
            f"  {row['id']:<12} {row['status']:<12} pm={row['package_manager']:<6} arches=[{arches}]"
        )
    lines.append("")

    ad = dashboard["replay_adapters"]
    lines.append(f"Replay adapters  default={ad['default_adapter']}")
    for row in ad["adapters"]:
        if row["enabled"]:
            flag = "ENABLED"
            level = "green"
        elif row.get("wired_in_build"):
            level = "yellow"
            flag = "WIRED"
        elif row.get("status") == "experimental":
            level = "yellow"
            flag = "REGISTERED"
        else:
            level = "red" if not row.get("registered") else "yellow"
            flag = "DISABLED"
        lines.append(
            f"  {row['id']:<24} {_status_color(level, use_color):<18} {flag} ({row.get('status', 'unknown')})"
        )
    lines.append("")

    lines.append("Lineage / gates")
    for row in dashboard["gates"]:
        lines.append(f"  {row['name']:<22} {_status_color(row['level'], use_color):<8} {row['detail']}")
    lines.append("")
    lines.append("Tip: run with --check for live validator status.")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    dashboard = build_dashboard(live=args.check)
    if args.json:
        print(json.dumps(dashboard, indent=2))
        return 0
    use_color = sys.stdout.isatty()
    print(render_text(dashboard, use_color))
    bad = [row for row in dashboard["gates"] if row["level"] == "red"]
    if args.check and bad:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
