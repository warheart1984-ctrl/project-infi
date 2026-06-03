#!/usr/bin/env python3
"""Naming genome gate — cross-layer linguistic validation for subsystem genomes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.linguistic_genome_lib import (  # noqa: E402
    LEGACY_SUFFIXES,
    MYTHIC_FORBIDDEN_IN_GENE,
    build_linguistic_record,
    extract_genome_layers,
    is_grandfathered_gene,
    is_grandfathered_module,
    load_aliases,
    load_grandfather_paths,
    load_json,
    validate_engineering_class,
    write_snapshot,
)

GENOME_DIR = _ROOT / "governance" / "subsystem_genomes"
STAGES_NEED_MODULE = frozenset({"prototype", "mvp", "governed"})


def validate_genome_linguistic(
    genome: dict,
    path: Path,
    aliases: dict,
    grandfather_paths: set[str],
    strict: bool,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    gene_file = path.name
    identity = genome.get("identity") or {}
    gene = identity.get("gene", "")
    stage = identity.get("stage", "")
    ssp = genome.get("ssp") or {}

    eng = ssp.get("engineering_class", "")
    mythic = ssp.get("mythic_label", "")

    if not eng:
        msg = f"{gene_file}: ssp.engineering_class missing"
        (errors if strict else warnings).append(msg)
    elif not validate_engineering_class(eng):
        errors.append(f"{gene_file}: invalid ssp.engineering_class {eng!r}")

    if not mythic:
        msg = f"{gene_file}: ssp.mythic_label missing"
        (errors if strict else warnings).append(msg)

    if not ssp.get("linguistic_version"):
        msg = f"{gene_file}: ssp.linguistic_version missing"
        (errors if strict else warnings).append(msg)

    if gene in aliases:
        expected = aliases[gene].get("engineering_class", "")
        if eng and expected and eng != expected:
            errors.append(
                f"{gene_file}: ssp.engineering_class {eng!r} != "
                f"alias registry {expected!r}"
            )

    if not is_grandfathered_gene(gene, aliases):
        for token in MYTHIC_FORBIDDEN_IN_GENE:
            if token in gene.split("_"):
                errors.append(
                    f"{gene_file}: non-grandfathered gene contains mythic token {token!r}"
                )

    for entry in (genome.get("runtime") or {}).get("surface") or []:
        if not isinstance(entry, dict) or entry.get("kind") != "module":
            continue
        mod = entry.get("path", "")
        if not mod:
            continue
        rel = mod.replace("\\", "/")
        if any(rel.endswith(s) for s in LEGACY_SUFFIXES):
            if not is_grandfathered_module(rel, gene, grandfather_paths):
                errors.append(
                    f"{gene_file}: runtime module {rel} not in grandfather registry"
                )

    if stage in STAGES_NEED_MODULE and eng:
        layers = extract_genome_layers(genome)
        mod = layers.get("module_path")
        if mod:
            src = _ROOT / mod
            if src.is_file():
                from tools.linguistic_genome_lib import extract_source_layers

                src_layers = extract_source_layers(src)
                header_eng = (src_layers.get("header") or {}).get("engineering", "")
                if header_eng and header_eng != eng:
                    warnings.append(
                        f"{gene_file}: source # Engineering: {header_eng!r} != "
                        f"ssp.engineering_class {eng!r}"
                    )
                elif not header_eng:
                    warnings.append(
                        f"{gene_file}: source missing # Engineering: header (Wave 2)"
                    )

    cs = ssp.get("concept_spec")
    if cs and eng:
        from tools.linguistic_genome_lib import extract_doc_layers

        doc = extract_doc_layers(_ROOT / cs)
        doc_eng = doc.get("engineering_class", "")
        if doc_eng and doc_eng != eng:
            warnings.append(
                f"{gene_file}: concept spec engineering {doc_eng!r} != genome {eng!r}"
            )

    if not eng and identity.get("display_name"):
        warnings.append(
            f"{gene_file}: display_name set but ssp.engineering_class missing"
        )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Naming genome gate")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument(
        "--snapshot",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Write linguistic snapshots when fingerprints change",
    )
    parser.add_argument("--gene", help="Validate single gene only")
    args = parser.parse_args()

    aliases = load_aliases(_ROOT)
    grandfather_paths = load_grandfather_paths(_ROOT)

    paths = sorted(GENOME_DIR.glob("*.genome.v1.json"))
    if args.gene:
        paths = [p for p in paths if _gene_matches(p, args.gene)]
        if not paths:
            print(f"ERROR: no genome for gene {args.gene!r}", file=sys.stderr)
            return 1

    all_errors: list[str] = []
    all_warnings: list[str] = []
    snapshots_written = 0

    for path in paths:
        genome = load_json(path)
        gene = (genome.get("identity") or {}).get("gene", "")
        errs, warns = validate_genome_linguistic(
            genome, path, aliases, grandfather_paths, args.strict
        )
        all_errors.extend(errs)
        all_warnings.extend(warns)

        if args.snapshot and gene:
            record = build_linguistic_record(gene, _ROOT)
            if record:
                out = write_snapshot(record, _ROOT)
                if out:
                    snapshots_written += 1

    for w in all_warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    for e in all_errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if all_errors:
        print(
            f"naming-genome-gate: FAIL ({len(all_errors)} error(s), "
            f"{len(all_warnings)} warning(s), {snapshots_written} snapshot(s))"
        )
        return 1

    print(
        f"naming-genome-gate: PASS ({len(paths)} genome(s), "
        f"{len(all_warnings)} warning(s), {snapshots_written} snapshot(s))"
    )
    return 0


def _gene_matches(path: Path, gene: str) -> bool:
    data = load_json(path)
    return (data.get("identity") or {}).get("gene") == gene


if __name__ == "__main__":
    sys.exit(main())
