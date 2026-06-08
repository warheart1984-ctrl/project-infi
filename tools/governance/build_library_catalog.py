"""Generate LIBRARY_CATALOG.json — cross-index for AAIS civilizational memory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "docs" / "proof" / "discovery" / "DISCOVERY_DOCUMENT_MANIFEST.json"
REGISTRY = REPO_ROOT / "governance" / "aais_library_registry.v1.json"
OUT = REPO_ROOT / "docs" / "proof" / "discovery" / "LIBRARY_CATALOG.json"


def _standing_from_doc(doc: dict) -> int:
    if doc.get("standing") is not None:
        return int(doc["standing"])
    from src.ugr.discovery.standing import standing_from_label

    return int(standing_from_label(str(doc.get("claim_label") or "asserted")))


def _load_manifest_documents() -> list[dict]:
    if not MANIFEST.exists():
        return []
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for doc in manifest.get("documents") or []:
        standing = _standing_from_doc(doc)
        if standing < 1:
            continue
        rows.append(
            {
                "kind": doc.get("kind") or "document",
                "slug": doc.get("slug"),
                "title": doc.get("title"),
                "standing": standing,
                "claim_label": doc.get("claim_label"),
                "library_admitted": bool(doc.get("library_admitted", standing >= 1)),
                "library_pattern_id": doc.get("library_pattern_id"),
                "library_reference": bool(doc.get("library_reference")),
                "rewards_suppressed": bool(doc.get("rewards_suppressed")),
                "proof_path": doc.get("proof_path"),
                "promotion_rule": doc.get("promotion_rule"),
                "source_path": doc.get("source_path") or doc.get("canonical_path"),
                "canonical_path": doc.get("canonical_path"),
            }
        )
    return rows


def _load_contributions() -> list[dict]:
    from src.ugr.discovery.contribution_store import ContributionDiscoveryStore
    from src.ugr.discovery.standing import standing_from_receipt

    store = ContributionDiscoveryStore()
    rows: list[dict] = []
    for entry in store.list_catalog(limit=10_000):
        receipt = dict(entry.get("receipt") or entry)
        payload = dict(receipt.get("payload") or entry)
        standing = int(standing_from_receipt(receipt))
        if standing < 1:
            continue
        rows.append(
            {
                "kind": "contribution",
                "contribution_id": entry.get("contribution_id") or entry.get("subsystem_id"),
                "contribution_type": entry.get("contribution_type"),
                "standing": standing,
                "claim_label": payload.get("claim_label"),
                "title": payload.get("title") or payload.get("workflow_id") or payload.get("role"),
                "first_discovered_at": entry.get("first_discovered_at"),
            }
        )
    return rows


def _load_plugin_libraries() -> list[dict]:
    if not REGISTRY.exists():
        return []
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for entry in reg.get("libraries") or []:
        ident = dict(entry.get("identity") or {})
        family = dict(entry.get("family") or {})
        rows.append(
            {
                "library_id": ident.get("library_id"),
                "display_name": ident.get("display_name"),
                "library_class": ident.get("library_class"),
                "category": family.get("category"),
            }
        )
    return rows


def build_catalog() -> dict:
    documents = _load_manifest_documents()
    contributions = _load_contributions()
    plugin_libraries = _load_plugin_libraries()
    return {
        "version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "totals": {
            "documents": len(documents),
            "contributions": len(contributions),
            "plugin_libraries": len(plugin_libraries),
        },
        "documents": documents,
        "contributions": contributions,
        "patterns": [],
        "plugin_libraries": plugin_libraries,
    }


def main() -> int:
    catalog = build_catalog()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT} "
        f"({catalog['totals']['documents']} docs, "
        f"{catalog['totals']['contributions']} contributions, "
        f"{catalog['totals']['plugin_libraries']} plugin libraries)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
