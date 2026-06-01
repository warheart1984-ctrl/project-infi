"""AI Factory CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ai_factory.common import DEFAULT_LEDGER_PATH, DEFAULT_RUNTIME_ROOT, json_stable
from ai_factory.orchestrator import (
    FactoryBuildError,
    build_status,
    deploy_active_build,
    revoke_build,
    run_build,
)
from ai_factory.proof_station import build_proof_manifest, run_verification_lanes
from ai_factory.spec import load_build_spec


def _print(payload: dict, *, output: str) -> None:
    if output == "json":
        print(json_stable(payload, pretty=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


def cmd_build(args: argparse.Namespace) -> int:
    try:
        result = run_build(
            spec_path=args.spec,
            repo_root=Path(args.repo_root),
            runtime_root=Path(args.runtime_root) if args.runtime_root else None,
            skip_pytest=args.skip_pytest,
            fixed_timestamp=args.fixed_timestamp or None,
            ledger_path=Path(args.ledger_path) if args.ledger_path else None,
        )
    except FactoryBuildError as exc:
        print(f"[ai-factory] build FAILED: {exc}", file=sys.stderr)
        return 1
    payload = {
        "mode": "build",
        "build_id": result.build_id,
        "output_dir": str(result.output_dir.resolve()),
        "claim_label": result.receipt.get("claim_label"),
        "receipt_path": str((result.output_dir / "AI_BUILD_RECEIPT.json").resolve()),
        "trace": result.trace,
    }
    _print(payload, output=args.output)
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    repo = Path(args.repo_root).resolve()
    spec = load_build_spec(args.spec)
    lanes = run_verification_lanes(
        repo_root=repo,
        spec=spec,
        skip_pytest=args.skip_pytest,
    )
    manifest = build_proof_manifest(
        spec=spec,
        lane_results=lanes,
        output_dir=Path(args.output_dir).resolve(),
        generated_at_utc=args.fixed_timestamp or None,
    )
    failed = [item for item in lanes if not item.get("passed")]
    payload = {"mode": "verify", "manifest": manifest, "failed_lanes": [item.get("lane") for item in failed]}
    _print(payload, output=args.output)
    return 1 if failed or manifest.get("deploy_blocked") else 0


def cmd_status(args: argparse.Namespace) -> int:
    payload = build_status(
        build_id=args.build_id or None,
        ledger_path=Path(args.ledger_path) if args.ledger_path else None,
        runtime_root=Path(args.runtime_root) if args.runtime_root else None,
    )
    payload["mode"] = "status"
    _print(payload, output=args.output)
    return 0


def cmd_deploy(args: argparse.Namespace) -> int:
    try:
        pointer = deploy_active_build(
            build_id=args.build_id,
            runtime_root=Path(args.runtime_root) if args.runtime_root else None,
            repo_root=Path(args.repo_root).resolve(),
            wolf_payload_root=Path(args.wolf_payload_root).resolve() if args.wolf_payload_root else None,
            wolf_deploy=bool(args.wolf),
            dry_run=bool(args.dry_run),
        )
    except FactoryBuildError as exc:
        print(f"[ai-factory] deploy FAILED: {exc}", file=sys.stderr)
        return 1
    payload = {
        "mode": "deploy",
        "build_id": args.build_id,
        "active_pointer": str(pointer.resolve()),
        "wolf_deploy": bool(args.wolf),
        "dry_run": bool(args.dry_run),
    }
    _print(payload, output=args.output)
    return 0


def cmd_revoke(args: argparse.Namespace) -> int:
    payload = revoke_build(
        build_id=args.build_id,
        runtime_root=Path(args.runtime_root) if args.runtime_root else None,
        ledger_path=Path(args.ledger_path) if args.ledger_path else None,
    )
    payload["mode"] = "revoke"
    _print(payload, output=args.output)
    return 0


def cmd_bundle_export(args: argparse.Namespace) -> int:
    build_id = args.build_id
    root = Path(args.runtime_root or DEFAULT_RUNTIME_ROOT).expanduser().resolve()
    output_dir = root / build_id
    receipt_path = output_dir / "AI_BUILD_RECEIPT.json"
    if not receipt_path.is_file():
        print(f"[ai-factory] missing receipt for build {build_id}", file=sys.stderr)
        return 1
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    payload = {
        "manifest_version": "ai_factory.bundle_export.v1",
        "mode": "bundle-export",
        "build_id": build_id,
        "claim_label": receipt.get("claim_label"),
        "hash_manifest": receipt.get("hash_manifest"),
        "proof_bundle_ref": receipt.get("proof_bundle_ref"),
        "output_dir": str(output_dir.resolve()),
    }
    if args.write:
        target = Path(args.write).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json_stable(payload, pretty=True) + "\n", encoding="utf-8")
        payload["bundle_export_path"] = str(target)
    _print(payload, output=args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Factory v1 — governed mind fabrication")
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--runtime-root", default=str(DEFAULT_RUNTIME_ROOT), help="factory output root")
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH), help="factory ledger path")
    parser.add_argument("--output", choices=("json", "text"), default="text")
    parser.add_argument("--fixed-timestamp", default="", help="deterministic UTC timestamp for receipts")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="run full factory pipeline")
    build.add_argument("--spec", required=True, help="path to YAML or JSON build spec")
    build.add_argument("--skip-pytest", action="store_true", help="skip verification lanes")
    build.add_argument("--repo-root", default=".", help="repository root")
    build.add_argument("--runtime-root", default=str(DEFAULT_RUNTIME_ROOT), help="factory output root")
    build.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH), help="factory ledger path")
    build.add_argument("--output", choices=("json", "text"), default="text")
    build.add_argument("--fixed-timestamp", default="", help="deterministic UTC timestamp for receipts")
    build.set_defaults(func=cmd_build)

    verify = sub.add_parser("verify", help="run verification lanes only")
    verify.add_argument("--spec", required=True)
    verify.add_argument("--output-dir", default=".runtime/ai_factory/verify")
    verify.add_argument("--skip-pytest", action="store_true")
    verify.set_defaults(func=cmd_verify)

    status = sub.add_parser("status", help="read ledger and receipt status")
    status.add_argument("--build-id", default="", help="optional build id")
    status.set_defaults(func=cmd_status)

    deploy = sub.add_parser("deploy", help="point active build pointer at a completed build")
    deploy.add_argument("--build-id", required=True)
    deploy.add_argument("--wolf", action="store_true", help="promote build into wolf-cog-os payload (v1.1)")
    deploy.add_argument("--wolf-payload-root", default="", help="override wolf payload config root")
    deploy.add_argument("--dry-run", action="store_true", help="validate wolf deploy without writing")
    deploy.set_defaults(func=cmd_deploy)

    revoke = sub.add_parser("revoke", help="revoke a build receipt")
    revoke.add_argument("--build-id", required=True)
    revoke.set_defaults(func=cmd_revoke)

    export = sub.add_parser("bundle-export", help="export hash manifest for a build")
    export.add_argument("--build-id", required=True)
    export.add_argument("--write", default="", help="optional output path")
    export.set_defaults(func=cmd_bundle_export)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
