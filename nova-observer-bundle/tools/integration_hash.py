#!/usr/bin/env python3
"""Mission #002 integration hash — stdlib only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def get_cursor_version() -> str:
    return os.environ.get("CURSOR_VERSION", "unknown")


def get_nova_version() -> str:
    return os.environ.get("NOVA_VERSION", "unknown")


def get_nemotron_model() -> str:
    return os.environ.get("NEMOTRON_MODEL", "Nemotron Ultra")


def get_protocol_version() -> str:
    return "1.0"


def get_adapter_version() -> str:
    return os.environ.get("NOVA_ADAPTER_VERSION", "1.0")


def get_tunnel_url(bundle_root: Path, explicit: str | None = None) -> str:
    if explicit:
        return explicit.strip()
    tunnel_file = bundle_root / "tunnel_url.txt"
    if not tunnel_file.exists():
        return "unknown"
    for line in tunnel_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        return stripped
    return "unknown"


def compute_integration_hash(metadata: dict[str, str]) -> str:
    payload = json.dumps(metadata, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_metadata(*, bundle_root: Path, tunnel_url: str | None = None) -> dict[str, str]:
    return {
        "cursor_version": get_cursor_version(),
        "nova_version": get_nova_version(),
        "nemotron_model": get_nemotron_model(),
        "adapter_version": get_adapter_version(),
        "protocol_version": get_protocol_version(),
        "tunnel_url": get_tunnel_url(bundle_root, tunnel_url),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute Mission #002 integration hash.")
    parser.add_argument("--tunnel-url", help="Override tunnel URL (mission coordinator).")
    parser.add_argument(
        "--write-expected",
        action="store_true",
        help="Write SHA256 to expected_integration_hash.txt (coordinator only).",
    )
    args = parser.parse_args()

    bundle_root = Path(__file__).resolve().parents[1]
    metadata = build_metadata(bundle_root=bundle_root, tunnel_url=args.tunnel_url)
    digest = compute_integration_hash(metadata)

    print("Integration metadata:")
    print(json.dumps(metadata, indent=2, sort_keys=True))
    print("\nSHA256 integration hash:")
    print(digest)

    observed_file = bundle_root / "integration_hash_observed.txt"
    observed_file.write_text(digest + "\n", encoding="utf-8")
    print(f"\nObserved hash written to: {observed_file}")

    if args.write_expected:
        expected_file = bundle_root / "expected_integration_hash.txt"
        body = (
            "# Mission #002 expected integration hash\n"
            "# Regenerate when tunnel_url.txt changes (mission coordinator).\n"
            "# Observer: run `python tools/integration_hash.py` and compare to SHA256 below.\n"
            "\n"
            f"SHA256: {digest}\n"
        )
        expected_file.write_text(body, encoding="utf-8")
        print(f"Expected hash written to: {expected_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
