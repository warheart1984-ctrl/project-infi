"""Register a library reference pattern in AAIS discovery (no registration rewards)."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from src.ugr.discovery.contribution_discovery import ContributionDiscoveryService
from src.ugr.discovery.contribution_spec import ContributionSpec, contribution_id_from_spec
from src.ugr.discovery.standing import (
    Standing,
    enrich_payload_with_standing,
    label_from_standing,
    library_admitted,
    standing_from_label,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DISCOVERY_DIR = REPO_ROOT / "docs" / "proof" / "discovery"
PACKETS_DIR = DISCOVERY_DIR / "packets"
RECEIPTS_DIR = DISCOVERY_DIR / "receipts"
MANIFEST_PATH = DISCOVERY_DIR / "DISCOVERY_DOCUMENT_MANIFEST.json"

DEFAULT_OPERATOR_ID = "operator:jon-halstead"
DEFAULT_POD_ID = "pod:jon-halstead"
DEFAULT_TENANT_ID = "global"
DEFAULT_AAIS_ID = "aais-primary"

DEFAULT_PATTERN = {
    "slug": "multi_model_orchestration_pattern",
    "title": "Multi-Model Orchestration Pattern",
    "canonical_path": "docs/architecture/MULTI_MODEL_ORCHESTRATION_PATTERN.md",
    "library_pattern_id": "multi_model_orchestration",
    "standing": int(Standing.ASSERTED),
}


def slugify(name: str) -> str:
    stem = Path(name).stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "_", stem)
    stem = re.sub(r"_+", "_", stem).strip("_")
    return stem[:120] or "library_pattern"


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def relative_repo_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def proof_packet_path(slug: str) -> Path:
    return PACKETS_DIR / f"{slug.upper()}_DISCOVERY_PROOF.md"


def write_proof_packet(
    *,
    slug: str,
    title: str,
    canonical_path: Path,
    digest: str,
    size: int,
    claim_label: str,
    standing: int,
    library_pattern_id: str,
) -> Path:
    packet = proof_packet_path(slug)
    rel_canonical = relative_repo_path(canonical_path)
    rel_packet = relative_repo_path(packet)
    packet.write_text(
        f"""# {title} — Library Pattern Proof Packet

Claim: Canonical pattern registered as governed Proof-of-Discovery evidence under UGR contribution type `proof`, attested by Discovery Pod **Jon Halstead**.

Claim status: **{claim_label}** (standing {standing}; artifact hash-anchored; validator pass).

This entry is a **library reference pattern**. Registration rewards are suppressed for the seeder. Matcher rewards (`library_pattern_matched`) issue to **any operator** for **each distinct qualifying contribution** that matches `library_pattern_id: {library_pattern_id}` — repeatable per contribution, not one-time per person.

## Discovery Pod

| Field | Value |
|---|---|
| Pod ID | `{DEFAULT_POD_ID}` |
| Display name | Jon Halstead |
| Operator ID | `{DEFAULT_OPERATOR_ID}` |

## Canonical artifact

| Field | Value |
|---|---|
| Title | {title} |
| Path | `{rel_canonical}` |
| SHA256 | `{digest}` |
| Size | {size:,} bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `kind` | `library_pattern` |
| `library_reference` | `true` |
| `rewards_suppressed` | `true` |
| `library_pattern_id` | `{library_pattern_id}` |
| `library_pattern_slug` | `{slug}` |
| `canonical_path` | `{rel_canonical}` |
| `proof_path` | `{rel_packet}` |
| `claim_label` | `{claim_label}` |
| `standing` | `{standing}` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `{DEFAULT_POD_ID}` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`
- `deploy/ugr/discovery-proof-promotion.json` (`library_patterns`)

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('{rel_canonical}'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
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
        "library_patterns": sum(1 for doc in documents if doc.get("kind") == "library_pattern"),
        "library_admitted": sum(1 for doc in documents if doc.get("library_admitted")),
    }
    manifest["updated_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def upsert_manifest_entry(manifest: dict, entry: dict) -> None:
    documents = list(manifest.get("documents") or [])
    slug = str(entry.get("slug") or "")
    replaced = False
    for idx, doc in enumerate(documents):
        if str(doc.get("slug") or "") == slug:
            documents[idx] = {**doc, **entry}
            replaced = True
            break
    if not replaced:
        documents.append(entry)
    manifest["documents"] = documents


def register_library_pattern(
    service: ContributionDiscoveryService,
    *,
    slug: str,
    title: str,
    canonical_path: Path,
    library_pattern_id: str,
    standing: int,
    dry_run: bool,
) -> dict:
    if not canonical_path.is_file():
        raise FileNotFoundError(f"canonical path not found: {canonical_path}")

    digest = sha256_file(canonical_path)
    size = canonical_path.stat().st_size
    claim_label = label_from_standing(standing)

    packet = write_proof_packet(
        slug=slug,
        title=title,
        canonical_path=canonical_path,
        digest=digest,
        size=size,
        claim_label=claim_label,
        standing=standing,
        library_pattern_id=library_pattern_id,
    )
    rel_packet = relative_repo_path(packet)
    rel_canonical = relative_repo_path(canonical_path)

    payload = enrich_payload_with_standing(
        {
            "title": title,
            "slug": slug,
            "kind": "library_pattern",
            "library_reference": True,
            "rewards_suppressed": True,
            "library_pattern_id": library_pattern_id,
            "library_pattern_slug": slug,
            "canonical_path": rel_canonical,
            "proof_path": rel_packet,
            "discovery_pod_id": DEFAULT_POD_ID,
            "source_document_path": rel_canonical,
            "source_sha256": digest,
        },
        standing=standing,
        claim_label=claim_label,
    )
    spec = ContributionSpec(contribution_type="proof", payload=payload)
    contribution_id = contribution_id_from_spec(spec)
    admitted = library_admitted(standing)

    entry = {
        "slug": slug,
        "title": title,
        "kind": "library_pattern",
        "library_pattern_id": library_pattern_id,
        "library_reference": True,
        "rewards_suppressed": True,
        "canonical_path": rel_canonical,
        "source_path": rel_canonical,
        "proof_path": rel_packet,
        "sha256": digest,
        "size_bytes": size,
        "standing": standing,
        "claim_label": claim_label,
        "library_admitted": admitted,
        "contribution_id": contribution_id,
    }
    if dry_run:
        entry["status"] = "dry_run"
        return entry

    if standing == int(Standing.DENIED):
        entry["status"] = "excluded"
        entry["summary"] = "library standing denied — discovery store skipped"
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
    entry["operator_rewards"] = result.get("operator_rewards")
    entry["library_pattern_rewards"] = result.get("library_pattern_rewards")

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
                        "operator_rewards": result.get("operator_rewards"),
                        "library_pattern_rewards": result.get("library_pattern_rewards"),
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        entry["receipt_path"] = relative_repo_path(receipt_path)
        entry["receipt_id"] = receipt.get("receipt_id")
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", default=DEFAULT_PATTERN["slug"])
    parser.add_argument("--title", default=DEFAULT_PATTERN["title"])
    parser.add_argument(
        "--canonical-path",
        default=DEFAULT_PATTERN["canonical_path"],
        help="Repo-relative path to canonical markdown pattern doc",
    )
    parser.add_argument(
        "--pattern-id",
        default=DEFAULT_PATTERN["library_pattern_id"],
        dest="library_pattern_id",
    )
    parser.add_argument(
        "--standing",
        type=int,
        default=DEFAULT_PATTERN["standing"],
        choices=(1, 2, 3),
    )
    parser.add_argument("--claim-label", default=None, choices=("hypothetical", "asserted", "proven"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    standing = int(standing_from_label(args.claim_label)) if args.claim_label else int(args.standing)
    canonical = REPO_ROOT / str(args.canonical_path).replace("\\", "/")
    slug = slugify(args.slug) if args.slug != DEFAULT_PATTERN["slug"] else str(args.slug)

    service = ContributionDiscoveryService()
    entry = register_library_pattern(
        service,
        slug=slug,
        title=str(args.title),
        canonical_path=canonical,
        library_pattern_id=str(args.library_pattern_id),
        standing=standing,
        dry_run=bool(args.dry_run),
    )

    if not args.dry_run:
        manifest = load_manifest()
        upsert_manifest_entry(manifest, entry)
        save_manifest(manifest)

    print(json.dumps(entry, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
