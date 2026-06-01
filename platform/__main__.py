"""CLI entry: python -m platform serve | worker | replay"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="platform")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Run Platform API")
    serve.add_argument("--host", default="")
    serve.add_argument("--port", type=int, default=0)

    sub.add_parser("worker", help="Run platform job worker")

    replay = sub.add_parser("replay", help="Cross-machine replay runner")
    replay.add_argument("--manifest", required=True)

    billing = sub.add_parser("billing", help="Billing export")
    billing_sub = billing.add_subparsers(dest="billing_cmd", required=True)
    export = billing_sub.add_parser("export")
    export.add_argument("--org", required=True)
    export.add_argument("--month", required=True)
    export.add_argument("--output", default="")

    ledger = sub.add_parser("ledger", help="Platform ledger v2")
    ledger_sub = ledger.add_subparsers(dest="ledger_cmd", required=True)
    ledger_export = ledger_sub.add_parser("export")
    ledger_export.add_argument("--org", required=True)
    ledger_export.add_argument("--output", default="")

    compliance = sub.add_parser("export", help="Compliance exports")
    compliance_sub = compliance.add_subparsers(dest="export_cmd", required=True)
    comp = compliance_sub.add_parser("compliance")
    comp.add_argument("--org", required=True)
    comp.add_argument("--kind", choices=("audit", "attestations"), default="audit")
    comp.add_argument("--output", default="")

    args = parser.parse_args(argv)

    if args.command == "serve":
        import uvicorn

        from platform.settings import PlatformSettings

        cfg = PlatformSettings.from_env()
        host = args.host or cfg.api_host
        port = args.port or cfg.api_port
        uvicorn.run("platform.api:create_app", factory=True, host=host, port=port)
        return 0

    if args.command == "worker":
        from platform.worker import run_worker

        run_worker()
        return 0

    if args.command == "replay":
        from platform.replay import run_replay

        return run_replay(manifest_path=args.manifest)

    if args.command == "billing" and args.billing_cmd == "export":
        from pathlib import Path

        from platform.billing.aggregator import write_usage_csv
        from platform.service import PlatformService

        svc = PlatformService()
        out = Path(args.output or f".runtime/platform/billing/{args.org}-{args.month}.csv")
        write_usage_csv(store=svc.store, org_id=args.org, month=args.month, output=out)
        print(str(out))
        return 0

    if args.command == "ledger" and args.ledger_cmd == "export":
        from pathlib import Path

        from platform.ledger.writer import export_ledger_jsonl
        from platform.service import PlatformService

        svc = PlatformService()
        text = export_ledger_jsonl(store=svc.store, org_id=args.org)
        out = Path(args.output or f".runtime/platform/ledger/{args.org}.jsonl")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(str(out))
        return 0

    if args.command == "export" and args.export_cmd == "compliance":
        from pathlib import Path

        from platform.service import PlatformService
        from platform.sovereign.exports import export_attestations_csv, export_audit_csv

        svc = PlatformService()
        if args.kind == "attestations":
            text = export_attestations_csv(store=svc.store, org_id=args.org)
            default = f".runtime/platform/exports/{args.org}-attestations.csv"
        else:
            text = export_audit_csv(store=svc.store, org_id=args.org)
            default = f".runtime/platform/exports/{args.org}-audit.csv"
        out = Path(args.output or default)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(str(out))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
