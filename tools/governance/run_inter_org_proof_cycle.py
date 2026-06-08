#!/usr/bin/env python
"""Inter-org proof cycle — Stage 19 witness + peer observe audit trail."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.peer_substrate_client import observe_all_peers, peer_base_urls  # noqa: E402


def _load_witness_bundles(bundle_dir: Path) -> list[dict]:
    bundles: list[dict] = []
    if not bundle_dir.is_dir():
        return bundles
    for path in sorted(bundle_dir.glob("**/*")):
        if path.suffix.lower() not in {".json", ".md"}:
            continue
        if path.suffix == ".json":
            try:
                doc = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(doc, dict):
                    doc["_path"] = str(path.relative_to(bundle_dir))
                    bundles.append(doc)
            except json.JSONDecodeError:
                bundles.append({"_path": str(path.relative_to(bundle_dir)), "parse_error": True})
    return bundles


def _distinct_witness_domains(bundles: list[dict]) -> list[str]:
    domains: set[str] = set()
    for bundle in bundles:
        for key in ("witness_org_domain", "org_domain", "operator_org_domain"):
            val = bundle.get(key)
            if isinstance(val, str) and val.strip():
                domains.add(val.strip())
        witnesses = bundle.get("external_witnesses") or bundle.get("witnesses") or []
        if isinstance(witnesses, list):
            for w in witnesses:
                if isinstance(w, dict):
                    d = w.get("witness_org_domain") or w.get("org_domain")
                    if isinstance(d, str) and d.strip():
                        domains.add(d.strip())
    return sorted(domains)


def run_proof_cycle(*, witness_bundle: Path, require_peers: bool) -> dict:
    peers = peer_base_urls()
    peer_results = observe_all_peers() if peers else []
    bundles = _load_witness_bundles(witness_bundle)
    domains = _distinct_witness_domains(bundles)
    peer_ok = all(r.get("ok") for r in peer_results) if peer_results else not require_peers
    witness_ok = len(domains) >= 1 or not require_peers
    green = peer_ok and witness_ok
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "peer_urls": peers,
        "peer_results": peer_results,
        "witness_bundle_dir": str(witness_bundle),
        "witness_bundle_count": len(bundles),
        "distinct_witness_domains": domains,
        "checks": {
            "peer_diplomacy_ok": peer_ok,
            "witness_domains_ok": witness_ok,
        },
        "status": "green" if green else "red",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--witness-bundle",
        type=Path,
        default=ROOT / "out",
        help="Directory containing witness Trust Bundle JSON artifacts",
    )
    parser.add_argument(
        "--require-peers",
        action="store_true",
        help="Fail if AAIS_PEER_BASE_URLS empty or any peer observe fails",
    )
    parser.add_argument(
        "--require-witnesses",
        action="store_true",
        help="Fail if no distinct witness_org_domain found in bundle dir",
    )
    args = parser.parse_args(argv)

    summary = run_proof_cycle(
        witness_bundle=args.witness_bundle,
        require_peers=args.require_peers,
    )
    if args.require_witnesses and not summary["checks"]["witness_domains_ok"]:
        summary["status"] = "red"

    date_slug = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    audit = ROOT / "docs" / "audit" / f"STAGE19_PROOF_CYCLE_{date_slug}.md"
    audit.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Stage 19 inter-org proof cycle — {date_slug}",
        "",
        f"Status: **{summary['status']}**",
        "",
        "## Peer diplomacy",
        "",
        f"- Peer URLs: `{summary['peer_urls']}`",
        f"- Peer diplomacy OK: `{summary['checks']['peer_diplomacy_ok']}`",
        "",
        "## Witness bundles",
        "",
        f"- Bundle dir: `{summary['witness_bundle_dir']}`",
        f"- Distinct witness domains: `{summary['distinct_witness_domains']}`",
        "",
        "## Raw summary",
        "",
        "```json",
        json.dumps(summary, indent=2),
        "```",
        "",
    ]
    audit.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Audit: {audit}")
    return 0 if summary["status"] == "green" else 1


if __name__ == "__main__":
    sys.exit(main())
