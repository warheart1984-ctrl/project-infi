#!/usr/bin/env python3
"""Validate OS-agnostic Forge replay substrate ISO contracts."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_LIB_DIR = _SCRIPT_DIR / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from substrate_classify import (  # noqa: E402
    classify_with_confidence,
    detect_substrate,
    registry_contract_version,
    resolve_spec,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Forge replay substrate ISO.")
    parser.add_argument("--iso", required=True, help="Path to substrate/replay ISO.")
    parser.add_argument(
        "--substrate-id",
        default="auto",
        help="Substrate id from registry, or auto.",
    )
    parser.add_argument(
        "--registry",
        default="wolf-cog-os/forge/substrates/registry.json",
        help="Substrate registry JSON path.",
    )
    parser.add_argument("--mode", choices=["warn", "fail"], default="fail")
    parser.add_argument("--output", default="")
    return parser.parse_args()


def _iso_paths(iso: Path) -> set[str]:
    if not shutil.which("xorriso"):
        raise RuntimeError("xorriso not available for substrate inspection")
    proc = subprocess.run(
        ["xorriso", "-indev", str(iso), "-find", "/", "-type", "f"],
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "xorriso find failed")
    paths: set[str] = set()
    for line in proc.stdout.splitlines():
        line = line.strip().strip("'\"")
        if not line or line.startswith("xorriso"):
            continue
        if line.startswith("/"):
            line = line[1:]
        paths.add(line.replace("\\", "/"))
    return paths


def _validate_layout(spec: dict, paths: set[str], effective_id: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    detect = spec.get("detect", {})
    glob_ok = any(
        any(fnmatch_match(path, pattern) for path in paths) for pattern in detect.get("path_globs", [])
    )
    any_ok = any(any(needle in path for path in paths) for needle in detect.get("path_any", []))
    marker_ok = any(marker in paths for marker in detect.get("path_markers", []))
    if paths and not glob_ok and not marker_ok:
        findings.append({"level": "error", "message": f"no squashfs/layout matched for substrate {effective_id}"})
    if paths and not any_ok and not marker_ok:
        findings.append({"level": "error", "message": f"no live boot paths matched for substrate {effective_id}"})
    return findings


def fnmatch_match(path: str, pattern: str) -> bool:
    import fnmatch

    return fnmatch.fnmatch(path, pattern)


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    iso_path = Path(args.iso)
    if not iso_path.is_file():
        print(f"ERROR: substrate ISO not found: {iso_path}", file=sys.stderr)
        return 2

    registry_path = repo_root / args.registry
    registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.is_file() else {"substrates": {}}
    contract_version = registry_contract_version(registry)
    requested = args.substrate_id
    findings: list[dict[str, str]] = []
    status = "pass"

    size = iso_path.stat().st_size
    try:
        paths = _iso_paths(iso_path)
    except Exception as exc:
        findings.append({"level": "error", "message": str(exc)})
        status = "fail"
        paths = set()

    classification = classify_with_confidence(registry, paths) if paths else {
        "substrate_id": registry.get("default_substrate_id", "generic-live-squashfs"),
        "confidence": 0.0,
        "method": "no-paths",
        "candidates": [],
    }
    detected = classification["substrate_id"]
    resolved_id = requested if requested not in ("", "auto") else detected
    effective_id, spec = resolve_spec(registry, resolved_id or registry.get("default_substrate_id", "generic-live-squashfs"))

    min_bytes = int(spec.get("min_bytes", 0))
    if min_bytes and size < min_bytes:
        findings.append({"level": "error", "message": f"ISO too small: {size} < min_bytes {min_bytes}"})
        status = "fail"

    findings.extend(_validate_layout(spec, paths, effective_id))

    if requested not in ("", "auto") and detected and detected != requested and status == "pass":
        findings.append(
            {
                "level": "warning",
                "message": (
                    f"classification={detected} (confidence={classification['confidence']}) "
                    f"differs from requested={requested}"
                ),
            }
        )

    result = {
        "validator": contract_version,
        "registry_version": registry.get("registry_version", "substrate-registry.v1"),
        "status": status if args.mode == "fail" or status == "pass" else "warn",
        "iso": str(iso_path.resolve()),
        "size_bytes": size,
        "requested_substrate_id": requested,
        "detected_substrate_id": detected,
        "effective_substrate_id": effective_id,
        "classification": classification,
        "replay_adapter": spec.get("replay_adapter", ""),
        "substrate_class": spec.get("class", ""),
        "substrate_family": spec.get("family", ""),
        "findings": findings,
    }

    if args.output:
        out = repo_root / args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(
        "Substrate validation:"
        f" status={result['status']}, effective={effective_id}, detected={detected or 'unknown'},"
        f" confidence={classification.get('confidence', 0)}, size={size}"
    )
    for finding in findings:
        print(f"[{finding['level'].upper()}] {finding['message']}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
