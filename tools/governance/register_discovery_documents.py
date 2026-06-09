"""Register operator PDFs as UGR Proof-of-Discovery contributions."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from src.ugr.discovery.contribution_discovery import ContributionDiscoveryService
from src.ugr.discovery.contribution_spec import contribution_id_from_spec, ContributionSpec
from src.ugr.discovery.proof_promotion import (
    load_promotion_policy,
    rejection_source_for_rule,
    resolve_standing,
    should_transition_standing,
)
from src.rls.falsity_registry import FalsityRegistry
from src.ugr.discovery.standing import (
    Standing,
    enrich_payload_with_standing,
    label_from_standing,
    library_admitted,
    standing_from_label,
)
from src.ugr.discovery.standing_verification import probe_document_verification

REPO_ROOT = Path(__file__).resolve().parents[2]
DISCOVERY_DIR = REPO_ROOT / "docs" / "proof" / "discovery"
PACKETS_DIR = DISCOVERY_DIR / "packets"
RECEIPTS_DIR = DISCOVERY_DIR / "receipts"
MANIFEST_PATH = DISCOVERY_DIR / "DISCOVERY_DOCUMENT_MANIFEST.json"

DEFAULT_SCAN_ROOTS = (
    REPO_ROOT,
    REPO_ROOT / "docs" / "fieldguide",
)

SKIP_PDF_NAMES: frozenset[str] = frozenset()

DEFAULT_OPERATOR_ID = "operator:jon-halstead"
DEFAULT_POD_ID = "pod:jon-halstead"
DEFAULT_TENANT_ID = "global"
DEFAULT_AAIS_ID = "aais-primary"


def slugify(name: str) -> str:
    stem = Path(name).stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "_", stem)
    stem = re.sub(r"_+", "_", stem).strip("_")
    return stem[:120] or "document"


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def discover_pdfs(scan_roots: tuple[Path, ...]) -> list[Path]:
    seen_hashes: dict[str, Path] = {}
    results: list[Path] = []
    for root in scan_roots:
        if not root.exists():
            continue
        for pdf in sorted(root.glob("*.pdf")):
            if pdf.name in SKIP_PDF_NAMES:
                continue
            digest = sha256_file(pdf)
            if digest in seen_hashes:
                continue
            seen_hashes[digest] = pdf
            results.append(pdf)
    return results


def relative_repo_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def proof_packet_path(slug: str) -> Path:
    return PACKETS_DIR / f"{slug.upper()}_DISCOVERY_PROOF.md"


def write_proof_packet(
    *,
    slug: str,
    title: str,
    source_path: Path,
    digest: str,
    size: int,
    claim_label: str,
    standing: int,
) -> Path:
    packet = proof_packet_path(slug)
    rel_source = relative_repo_path(source_path)
    rel_packet = relative_repo_path(packet)
    packet.write_text(
        f"""# {title} — Proof-of-Discovery Packet

Claim: Source PDF registered as governed Proof-of-Discovery evidence under UGR contribution type `proof`, attested by Discovery Pod **Jon Halstead**.

Claim status: **{claim_label}** (standing {standing}; artifact hash-anchored; validator pass).

## Discovery Pod

| Field | Value |
|---|---|
| Pod ID | `{DEFAULT_POD_ID}` |
| Display name | Jon Halstead |
| Operator ID | `{DEFAULT_OPERATOR_ID}` |

## Source artifact

| Field | Value |
|---|---|
| Title | {title} |
| Path | `{rel_source}` |
| SHA256 | `{digest}` |
| Size | {size:,} bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `{rel_packet}` |
| `claim_label` | `{claim_label}` |
| `standing` | `{standing}` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `{DEFAULT_POD_ID}` |
| `source_document_path` | `{rel_source}` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('{rel_source}'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
""",
        encoding="utf-8",
    )
    return packet


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {
        "manifest_version": "1.0",
        "authority": "docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md",
        "operator_id": DEFAULT_OPERATOR_ID,
        "discovery_pod_id": DEFAULT_POD_ID,
        "documents": [],
    }


def save_manifest(manifest: dict) -> None:
    documents = manifest.get("documents", [])
    manifest["totals"] = {
        "documents_registered": len(documents),
        "denied": sum(
            1
            for doc in documents
            if int(doc.get("standing", standing_from_label(doc.get("claim_label"))) or 0)
            == int(Standing.DENIED)
        ),
        "hypothetical": sum(
            1
            for doc in documents
            if int(doc.get("standing", standing_from_label(doc.get("claim_label"))) or 0)
            == int(Standing.HYPOTHETICAL)
        ),
        "asserted": sum(
            1
            for doc in documents
            if int(doc.get("standing", standing_from_label(doc.get("claim_label"))) or 0)
            == int(Standing.ASSERTED)
        ),
        "proven": sum(
            1
            for doc in documents
            if int(doc.get("standing", standing_from_label(doc.get("claim_label"))) or 0)
            == int(Standing.PROVEN)
        ),
        "library_admitted": sum(1 for doc in documents if doc.get("library_admitted")),
    }
    manifest["updated_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def resolve_document_standing(
    doc_meta: dict,
    *,
    policy: dict,
    auto_promote: bool,
    force_label: str | None = None,
) -> tuple[int, str, str | None, dict]:
    verification = probe_document_verification(doc_meta)
    if force_label:
        standing = int(standing_from_label(force_label))
        return standing, force_label, None, verification
    standing, label, rule_id = resolve_standing(
        doc_meta,
        policy=policy,
        verification_context=verification,
        auto_promote=auto_promote,
    )
    return standing, label, rule_id, verification


def register_document(
    service: ContributionDiscoveryService,
    *,
    slug: str,
    title: str,
    source_path: Path,
    digest: str,
    size: int,
    standing: int,
    claim_label: str,
    verification: dict | None,
    dry_run: bool,
    promotion_rule: str = "",
) -> dict:
    packet = write_proof_packet(
        slug=slug,
        title=title,
        source_path=source_path,
        digest=digest,
        size=size,
        claim_label=claim_label,
        standing=standing,
    )
    rel_packet = relative_repo_path(packet)
    claim_text = f"{title} ({slug})"
    rejection_source = rejection_source_for_rule(promotion_rule) if int(standing) == int(Standing.DENIED) else None
    payload = enrich_payload_with_standing(
        {
            "proof_path": rel_packet,
            "discovery_pod_id": DEFAULT_POD_ID,
            "source_document_path": relative_repo_path(source_path),
            "source_sha256": digest,
            "promotion_rule": promotion_rule or None,
        },
        standing=standing,
        claim_label=claim_label,
        rejection_source=rejection_source,
    )
    spec = ContributionSpec(contribution_type="proof", payload=payload)
    contribution_id = contribution_id_from_spec(spec)
    admitted = library_admitted(standing)
    entry = {
        "slug": slug,
        "title": title,
        "source_path": relative_repo_path(source_path),
        "proof_path": rel_packet,
        "sha256": digest,
        "size_bytes": size,
        "standing": standing,
        "claim_label": claim_label,
        "library_admitted": admitted,
        "verification": dict(verification or {}),
        "contribution_id": contribution_id,
    }
    if dry_run:
        entry["status"] = "dry_run"
        return entry

    if standing == int(Standing.DENIED):
        try:
            FalsityRegistry().record_falsified(
                text=claim_text,
                reason=f"discovery_denial:{promotion_rule or 'unspecified'}",
                rejection_source=rejection_source or "discovery_denial",
            )
        except Exception:
            pass
        entry["status"] = "excluded"
        entry["summary"] = "library standing denied — discovery store skipped"
        entry["promotion_rule"] = promotion_rule or None
        return entry

    result = service.discover(
        {
            "tenant_id": DEFAULT_TENANT_ID,
            "operator_id": DEFAULT_OPERATOR_ID,
            "aais_instance_id": DEFAULT_AAIS_ID,
            "contribution_type": "proof",
            "payload": spec.payload,
        }
    )
    entry["status"] = result.get("status")
    entry["summary"] = result.get("summary")
    entry["idempotent"] = bool(result.get("idempotent"))
    receipt = result.get("contribution_discovery_receipt") or {}
    if receipt:
        receipt_path = RECEIPTS_DIR / f"{slug}_discovery_receipt.json"
        receipt_path.write_text(
            json.dumps(
                {
                    "contribution_discovery_receipt": receipt,
                    "result_summary": {
                        "status": result.get("status"),
                        "summary": result.get("summary"),
                        "contribution_id": result.get("contribution_id"),
                        "contribution_type": result.get("contribution_type"),
                        "catalog_status": result.get("catalog_status"),
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        entry["receipt_path"] = relative_repo_path(receipt_path)
        entry["receipt_id"] = receipt.get("receipt_id")
        entry["verification"]["receipt_verified"] = bool(result.get("receipt_verified"))
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Scan and write packets only")
    parser.add_argument(
        "--claim-label",
        default=None,
        choices=("denied", "hypothetical", "asserted", "proven", "rejected"),
        help="Force this claim label for all new registrations (disables pattern auto-promote)",
    )
    parser.add_argument(
        "--no-auto-promote",
        action="store_true",
        help="Register new documents as asserted without pattern-based promotion",
    )
    parser.add_argument(
        "--no-upgrade-existing",
        action="store_true",
        help="Skip upgrading existing documents when standing policy changes",
    )
    args = parser.parse_args()

    PACKETS_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

    pdfs = discover_pdfs(DEFAULT_SCAN_ROOTS)
    manifest = load_manifest()
    documents_by_slug = {doc["slug"]: doc for doc in manifest.get("documents", []) if doc.get("slug")}
    known_digests = {
        doc.get("sha256") for doc in manifest.get("documents", []) if doc.get("sha256")
    }
    policy = load_promotion_policy()
    auto_promote = not args.no_auto_promote and args.claim_label is None
    upgrade_existing = not args.no_upgrade_existing and auto_promote
    service = ContributionDiscoveryService()

    registered: list[dict] = []
    promoted: list[dict] = []
    skipped = 0
    digest_to_slug = {
        doc.get("sha256"): doc.get("slug")
        for doc in manifest.get("documents", [])
        if doc.get("sha256") and doc.get("slug")
    }

    for pdf in pdfs:
        digest = sha256_file(pdf)
        slug = slugify(pdf.name)
        existing_slug = digest_to_slug.get(digest)
        existing = documents_by_slug.get(existing_slug or slug)

        if digest in known_digests and existing:
            if upgrade_existing:
                doc_meta = dict(existing)
                doc_meta.setdefault("title", pdf.stem)
                doc_meta.setdefault("source_path", relative_repo_path(pdf))
                changed, target_standing, target_label, rule_id = should_transition_standing(
                    doc_meta,
                    policy=policy,
                    verification_context=probe_document_verification(doc_meta),
                    auto_promote=auto_promote,
                )
                if changed:
                    entry = register_document(
                        service,
                        slug=existing.get("slug") or slug,
                        title=existing.get("title") or pdf.stem,
                        source_path=pdf,
                        digest=digest,
                        size=int(existing.get("size_bytes") or pdf.stat().st_size),
                        standing=target_standing,
                        claim_label=target_label,
                        verification=probe_document_verification(doc_meta),
                        dry_run=args.dry_run,
                        promotion_rule=rule_id,
                    )
                    entry["promotion_rule"] = rule_id
                    entry["promoted_from"] = existing.get("claim_label")
                    entry["standing_from"] = existing.get("standing")
                    promoted.append(entry)
                    documents_by_slug[entry["slug"]] = entry
                    continue
            skipped += 1
            continue

        doc_meta = {
            "title": pdf.stem,
            "slug": slug,
            "source_path": relative_repo_path(pdf),
        }
        standing, claim_label, promotion_rule, verification = resolve_document_standing(
            doc_meta,
            policy=policy,
            auto_promote=auto_promote,
            force_label=args.claim_label,
        )

        entry = register_document(
            service,
            slug=slug,
            title=pdf.stem,
            source_path=pdf,
            digest=digest,
            size=pdf.stat().st_size,
            standing=standing,
            claim_label=claim_label,
            verification=verification,
            dry_run=args.dry_run,
            promotion_rule=promotion_rule,
        )
        if promotion_rule:
            entry["promotion_rule"] = promotion_rule
        registered.append(entry)
        documents_by_slug[slug] = entry
        known_digests.add(digest)
        digest_to_slug[digest] = slug

    manifest["documents"] = sorted(
        documents_by_slug.values(),
        key=lambda item: item.get("title", ""),
    )
    if auto_promote:
        manifest["promotion_policy"] = str(policy.get("version", "1.0"))
    save_manifest(manifest)

    summary = {
        "registered": len(registered),
        "promoted": len(promoted),
        "skipped": skipped,
        "total": len(manifest["documents"]),
        "auto_promote": auto_promote,
    }
    print(json.dumps(summary, indent=2))
    for entry in registered + promoted:
        line = f"- {entry['slug']} -> {entry.get('status', 'written')} standing={entry.get('standing')}\n"
        import sys

        sys.stdout.buffer.write(line.encode("utf-8", errors="replace"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
