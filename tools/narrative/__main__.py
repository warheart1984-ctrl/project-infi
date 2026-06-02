"""Narrative Trust Pack CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.capabilities.narrative_trust_pack import (
    DEFAULT_NARRATIVE_ROOT,
    apply_signoff,
    build_pack_from_capability_output,
    load_pack,
    persist_pack,
    verify_pack_integrity,
)


def _emit(payload: dict, output: str | None) -> None:
    text = json.dumps(payload, sort_keys=True, indent=2)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def cmd_pack(args: argparse.Namespace) -> int:
    result_path = Path(args.from_capability_result).expanduser().resolve()
    output = json.loads(result_path.read_text(encoding="utf-8"))
    sf_path = args.story_forge_artifact or output.get("metadata_path")
    pack = build_pack_from_capability_output(
        output,
        pack_id=args.pack_id,
        author=args.author,
        story_forge_artifact_path=sf_path,
        root=Path(args.narrative_root) if args.narrative_root else None,
    )
    _emit({"mode": "pack", "pack": pack}, args.output)
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    pack = load_pack(args.pack_id, root=Path(args.narrative_root) if args.narrative_root else None)
    verify = verify_pack_integrity(pack)
    _emit({"mode": "verify", "pack_id": args.pack_id, **verify}, args.output)
    return 0 if verify.get("ok") else 1


def cmd_signoff(args: argparse.Namespace) -> int:
    root = Path(args.narrative_root) if args.narrative_root else None
    pack = load_pack(args.pack_id, root=root)
    pack = apply_signoff(pack, signoff_by=args.signoff_by, notes=args.notes or "")
    persist_pack(pack, root=root)
    _emit({"mode": "signoff", "pack": pack}, args.output)
    return 0 if pack.get("claim_label") == "proven" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Narrative Trust Pack tools")
    sub = parser.add_subparsers(dest="command", required=True)

    pack = sub.add_parser("pack")
    pack.add_argument("--from-capability-result", required=True)
    pack.add_argument("--pack-id", required=True)
    pack.add_argument("--author", default="operator")
    pack.add_argument("--story-forge-artifact")
    pack.add_argument("--narrative-root", default=str(DEFAULT_NARRATIVE_ROOT))
    pack.add_argument("--output")
    pack.set_defaults(func=cmd_pack)

    verify = sub.add_parser("verify")
    verify.add_argument("--pack-id", required=True)
    verify.add_argument("--narrative-root", default=str(DEFAULT_NARRATIVE_ROOT))
    verify.add_argument("--output")
    verify.set_defaults(func=cmd_verify)

    signoff = sub.add_parser("signoff")
    signoff.add_argument("--pack-id", required=True)
    signoff.add_argument("--signoff-by", required=True)
    signoff.add_argument("--notes", default="")
    signoff.add_argument("--narrative-root", default=str(DEFAULT_NARRATIVE_ROOT))
    signoff.add_argument("--output")
    signoff.set_defaults(func=cmd_signoff)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
