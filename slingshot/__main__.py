"""AI Slingshot CLI — preload, status, verify."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from slingshot.common import frame_path, packet_path, slingshot_case_dir
from slingshot.frame import build_slingshot_frame, load_slingshot_frame
from slingshot.impact import verify_slingshot_case
from slingshot.packet import build_slingshot_packet, load_slingshot_packet


def _emit(payload: dict, output: str | None) -> None:
    text = json.dumps(payload, sort_keys=True, indent=2)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def cmd_preload(args: argparse.Namespace) -> int:
    frame = build_slingshot_frame(
        case_id=args.case_id,
        repo_path=args.repo,
        trace_path=args.trace_path or "",
    )
    packet = None
    if not frame.get("launch_blocked"):
        packet = build_slingshot_packet(
            frame,
            {
                "authorized_goals": args.authorized_goals or ["analyze and propose remediation only"],
                "required_constraints": args.required_constraints or [],
            },
        )
    _emit(
        {
            "mode": "preload",
            "case_id": args.case_id,
            "launch_blocked": frame.get("launch_blocked"),
            "frame_path": str(frame_path(args.case_id)),
            "packet_path": str(packet_path(args.case_id)) if packet else None,
            "drift_count": frame.get("drift_count"),
            "claim_label": "asserted",
        },
        args.output,
    )
    return 0 if not frame.get("launch_blocked") else 1


def cmd_status(args: argparse.Namespace) -> int:
    case_dir = slingshot_case_dir(args.case_id)
    payload: dict = {"mode": "status", "case_id": args.case_id, "claim_label": "asserted"}
    frame_file = frame_path(args.case_id)
    packet_file = packet_path(args.case_id)
    if frame_file.is_file():
        frame = load_slingshot_frame(args.case_id)
        payload["frame"] = {
            "launch_blocked": frame.get("launch_blocked"),
            "drift_count": frame.get("drift_count"),
            "ma13_summary": frame.get("ma13_summary"),
        }
    else:
        payload["frame"] = None
    if packet_file.is_file():
        packet = load_slingshot_packet(args.case_id)
        payload["packet"] = {
            "expires_at_utc": packet.get("expires_at_utc"),
            "compose_mode": packet.get("compose_mode"),
        }
    else:
        payload["packet"] = None
    payload["artifacts_present"] = frame_file.is_file() and packet_file.is_file()
    _emit(payload, args.output)
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    frame = load_slingshot_frame(args.case_id) if frame_path(args.case_id).is_file() else {}
    repo = args.repo or frame.get("repo_path") or ""
    result = verify_slingshot_case(args.case_id, repo_path=repo or None)
    _emit(result, args.output)
    return 0 if result.get("ok") else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI Slingshot — governed workflow burst lane")
    sub = parser.add_subparsers(dest="command", required=True)

    preload = sub.add_parser("preload", help="Pullback: Mechanic scan + governance frame")
    preload.add_argument("--case-id", required=True)
    preload.add_argument("--repo", required=True)
    preload.add_argument("--trace-path", default="")
    preload.add_argument("--authorized-goals", nargs="*", default=None)
    preload.add_argument("--required-constraints", nargs="*", default=None)
    preload.add_argument("--output", default="")
    preload.set_defaults(func=cmd_preload)

    status = sub.add_parser("status", help="Show frame and packet status")
    status.add_argument("--case-id", required=True)
    status.add_argument("--output", default="")
    status.set_defaults(func=cmd_status)

    verify = sub.add_parser("verify", help="Verify artifact chain + optional replay")
    verify.add_argument("--case-id", required=True)
    verify.add_argument("--repo", default="")
    verify.add_argument("--output", default="")
    verify.set_defaults(func=cmd_verify)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
