"""Re-evaluate standing policy and reconcile discovery document claim labels."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.ugr.discovery.contribution_discovery import ContributionDiscoveryService
from src.ugr.discovery.contribution_store import ContributionDiscoveryStore
from src.ugr.discovery.proof_promotion import (
    load_promotion_policy,
    should_exclude_from_library,
    should_transition_standing,
)
from src.ugr.discovery.standing import Standing, library_admitted
from src.ugr.discovery.standing_verification import probe_document_verification

_REGISTER_PATH = REPO_ROOT / "tools" / "governance" / "register_discovery_documents.py"
_register_spec = importlib.util.spec_from_file_location("register_discovery_documents", _REGISTER_PATH)
_register_mod = importlib.util.module_from_spec(_register_spec)
assert _register_spec.loader is not None
_register_spec.loader.exec_module(_register_mod)

DEFAULT_SCAN_ROOTS = _register_mod.DEFAULT_SCAN_ROOTS
DEFAULT_TENANT_ID = _register_mod.DEFAULT_TENANT_ID
discover_pdfs = _register_mod.discover_pdfs
load_manifest = _register_mod.load_manifest
register_document = _register_mod.register_document
save_manifest = _register_mod.save_manifest
sha256_file = _register_mod.sha256_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Preview reconcile only")
    parser.add_argument("--no-auto-promote", action="store_true", help="Disable pattern policy")
    args = parser.parse_args()

    policy = load_promotion_policy()
    auto_promote = not args.no_auto_promote
    manifest = load_manifest()
    documents_by_slug = {doc["slug"]: doc for doc in manifest.get("documents", []) if doc.get("slug")}
    pdf_by_digest = {sha256_file(pdf): pdf for pdf in discover_pdfs(DEFAULT_SCAN_ROOTS)}
    service = ContributionDiscoveryService()
    store = ContributionDiscoveryStore(runtime_dir=REPO_ROOT / "runtime")

    promoted: list[dict] = []
    demoted: list[dict] = []
    excluded: list[dict] = []
    preview: list[dict] = []
    unchanged = 0

    for slug, doc in sorted(documents_by_slug.items()):
        verification = probe_document_verification(doc)
        exclude, exclude_rule = should_exclude_from_library(
            doc,
            policy=policy,
            verification_context=verification,
            auto_promote=auto_promote,
        )
        if exclude:
            if args.dry_run:
                preview.append(
                    {
                        "slug": slug,
                        "status": "would_exclude",
                        "from": doc.get("claim_label"),
                        "to": "denied",
                        "standing": 0,
                        "promotion_rule": exclude_rule,
                    }
                )
                continue
            cid = str(doc.get("contribution_id") or "").strip()
            if cid:
                store.withdraw_contribution(cid, reason=exclude_rule or "library_standing_denied")
            entry = {
                **doc,
                "standing": int(Standing.DENIED),
                "claim_label": "denied",
                "library_admitted": False,
                "status": "excluded",
                "promotion_rule": exclude_rule,
                "reconcile_action": "exclude",
            }
            documents_by_slug[slug] = entry
            excluded.append(entry)
            continue

        changed, target_standing, target_label, rule_id = should_transition_standing(
            doc,
            policy=policy,
            verification_context=verification,
            auto_promote=auto_promote,
        )
        if not changed:
            if doc.get("library_admitted") is None:
                doc["library_admitted"] = library_admitted(doc.get("standing", doc.get("claim_label")))
            unchanged += 1
            continue

        action = "promote" if target_standing > int(doc.get("standing", 0)) else "demote"
        pdf = pdf_by_digest.get(doc.get("sha256"))
        if pdf is None:
            preview.append(
                {
                    "slug": slug,
                    "status": "missing_source",
                    "action": action,
                    "target_claim_label": target_label,
                    "target_standing": target_standing,
                    "promotion_rule": rule_id,
                }
            )
            continue

        if args.dry_run:
            preview.append(
                {
                    "slug": slug,
                    "status": f"would_{action}",
                    "from": doc.get("claim_label"),
                    "to": target_label,
                    "standing": target_standing,
                    "promotion_rule": rule_id,
                }
            )
            continue

        entry = register_document(
            service,
            slug=slug,
            title=doc.get("title") or pdf.stem,
            source_path=pdf,
            digest=doc["sha256"],
            size=int(doc.get("size_bytes") or pdf.stat().st_size),
            standing=target_standing,
            claim_label=target_label,
            verification=verification,
            dry_run=False,
        )
        entry["promotion_rule"] = rule_id
        entry["reconciled_from"] = doc.get("claim_label")
        entry["standing_from"] = doc.get("standing")
        entry["reconcile_action"] = action
        documents_by_slug[slug] = entry
        if action == "promote":
            promoted.append(entry)
        else:
            demoted.append(entry)

    if not args.dry_run:
        manifest["documents"] = sorted(
            documents_by_slug.values(),
            key=lambda item: item.get("title", ""),
        )
        manifest["promotion_policy"] = str(policy.get("version", "1.0"))
        save_manifest(manifest)

    summary = {
        "promoted": len(promoted),
        "demoted": len(demoted),
        "excluded": len(excluded),
        "unchanged": unchanged,
        "preview": len(preview),
        "dry_run": args.dry_run,
        "auto_promote": auto_promote,
        "policy_version": policy.get("version"),
    }
    print(json.dumps(summary, indent=2))
    for item in preview + promoted + demoted + excluded:
        status = item.get("status", item.get("reconcile_action", item.get("claim_label")))
        line = (
            f"- {item['slug']}: {status} standing={item.get('standing')} "
            f"rule={item.get('promotion_rule')}\n"
        )
        sys.stdout.buffer.write(line.encode("utf-8", errors="replace"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
