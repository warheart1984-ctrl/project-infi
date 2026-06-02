#!/usr/bin/env python3
"""Subsystem genome gate — DNA validator for SSP Alt-4 registered families."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

GENOME_DIR = Path("governance/subsystem_genomes")
META_SCHEMA = Path("schemas/subsystem_genome.v1.json")

REQUIRED_TOP = {
    "subsystem_genome_version",
    "identity",
    "governance",
    "schema",
    "runtime",
    "proof",
    "lineage",
    "activation",
    "mutation",
}

STAGES = frozenset({"concept", "prototype", "mvp", "governed", "deprecated", "retired"})
POSTURES = frozenset({"asserted", "prototype", "mvp", "governed"})
SURFACE_KINDS = frozenset({"module", "cli", "api", "ui", "tool", "gate", "package", "sandbox"})


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_identity(identity: Any, gene_file: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(identity, dict):
        return [f"{gene_file}: identity must be object"]
    for key in ("gene", "version", "stage"):
        if key not in identity:
            errors.append(f"{gene_file}: identity missing {key}")
    stage = identity.get("stage")
    if stage not in STAGES:
        errors.append(f"{gene_file}: invalid identity.stage {stage!r}")
    gene = identity.get("gene")
    if isinstance(gene, str) and not gene.replace("_", "").isalnum():
        errors.append(f"{gene_file}: invalid identity.gene {gene!r}")
    return errors


def validate_governance(gov: Any, gene_file: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(gov, dict):
        return [f"{gene_file}: governance must be object"]
    for key in ("contracts", "invariants"):
        if key not in gov:
            errors.append(f"{gene_file}: governance missing {key}")
        elif not isinstance(gov[key], list) or len(gov[key]) < 1:
            errors.append(f"{gene_file}: governance.{key} must be non-empty array")
    return errors


def validate_schema_block(schema: Any, root: Path, gene_file: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(schema, dict) or "ref" not in schema:
        return [f"{gene_file}: schema.ref required"]
    ref = schema["ref"]
    if not isinstance(ref, str):
        return [f"{gene_file}: schema.ref must be string"]
    candidates = [
        root / ref,
        root / "docs/_future/ideas_pending" / ref.replace("schemas/", "schemas/"),
    ]
    if ref.startswith("schemas/"):
        candidates.append(root / "docs/_future/ideas_pending/schemas" / Path(ref).name)
    if not any(p.is_file() for p in candidates):
        errors.append(f"{gene_file}: schema not found: {ref}")
    return errors


def validate_runtime(runtime: Any, stage: str, gene_file: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(runtime, dict) or "surface" not in runtime:
        return [f"{gene_file}: runtime.surface required"]
    surface = runtime["surface"]
    if not isinstance(surface, list):
        return [f"{gene_file}: runtime.surface must be array"]
    if stage == "concept" and len(surface) > 0:
        errors.append(f"{gene_file}: concept stage must have empty runtime.surface")
    if stage in ("mvp", "governed") and len(surface) < 1:
        errors.append(f"{gene_file}: {stage} stage requires runtime.surface entries")
    for i, entry in enumerate(surface):
        if not isinstance(entry, dict):
            errors.append(f"{gene_file}: runtime.surface[{i}] must be object")
            continue
        kind = entry.get("kind")
        if kind not in SURFACE_KINDS:
            errors.append(f"{gene_file}: invalid surface kind {kind!r}")
        if not entry.get("path"):
            errors.append(f"{gene_file}: runtime.surface[{i}] missing path")
    return errors


def validate_proof(proof: Any, stage: str, gene_file: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(proof, dict):
        return [f"{gene_file}: proof must be object"]
    if "posture" not in proof:
        errors.append(f"{gene_file}: proof.posture required")
    elif proof["posture"] not in POSTURES:
        errors.append(f"{gene_file}: invalid proof.posture")
    if stage == "concept" and proof.get("posture") != "asserted":
        errors.append(f"{gene_file}: concept stage requires proof.posture asserted")
    bundles = proof.get("bundles")
    if not isinstance(bundles, list):
        errors.append(f"{gene_file}: proof.bundles must be array")
    elif stage in ("mvp", "governed") and len(bundles) < 1:
        errors.append(f"{gene_file}: {stage} stage requires proof.bundles")
    return errors


def validate_paths_exist(paths: list[str], root: Path, gene_file: str, label: str) -> list[str]:
    errors: list[str] = []
    for p in paths:
        if not isinstance(p, str):
            continue
        if not (root / p).is_file():
            errors.append(f"{gene_file}: missing {label}: {p}")
    return errors


def validate_genome(data: dict[str, Any], path: Path, root: Path) -> list[str]:
    gene_file = path.name
    errors: list[str] = []

    if data.get("subsystem_genome_version") != "subsystem_genome.v1":
        errors.append(f"{gene_file}: subsystem_genome_version must be subsystem_genome.v1")

    missing = REQUIRED_TOP - set(data.keys())
    if missing:
        errors.append(f"{gene_file}: missing top-level keys: {sorted(missing)}")

    errors.extend(validate_identity(data.get("identity"), gene_file))
    errors.extend(validate_governance(data.get("governance"), gene_file))
    errors.extend(validate_schema_block(data.get("schema"), root, gene_file))

    stage = (data.get("identity") or {}).get("stage", "")
    errors.extend(validate_runtime(data.get("runtime"), stage, gene_file))
    errors.extend(validate_proof(data.get("proof"), stage, gene_file))

    proof = data.get("proof") or {}
    bundles = proof.get("bundles") or []
    errors.extend(validate_paths_exist(bundles, root, gene_file, "proof bundle"))

    gov = data.get("governance") or {}
    errors.extend(validate_paths_exist(gov.get("contracts") or [], root, gene_file, "contract"))

    ssp = data.get("ssp") or {}
    for key in ("concept_spec", "mvp_plan", "active_doc"):
        if key in ssp and ssp[key]:
            if not (root / ssp[key]).is_file():
                errors.append(f"{gene_file}: missing ssp.{key}: {ssp[key]}")

    lineage = data.get("lineage") or {}
    if not isinstance(lineage.get("parents"), list) or not isinstance(lineage.get("children"), list):
        errors.append(f"{gene_file}: lineage.parents and lineage.children required")

    mutation = data.get("mutation")
    if not isinstance(mutation, dict) or "history" not in mutation:
        errors.append(f"{gene_file}: mutation.history required")

    if stage in ("deprecated", "retired"):
        ssp_eligible = ssp.get("summon_eligible", True)
        if ssp_eligible is not False:
            errors.append(f"{gene_file}: deprecated/retired must set ssp.summon_eligible false")

    return errors


def validate_lineage_symmetry(genomes: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    registered = set(genomes.keys())

    for gene, data in genomes.items():
        lineage = data.get("lineage") or {}
        for parent in lineage.get("parents") or []:
            if parent in registered and gene not in (genomes[parent].get("lineage") or {}).get("children", []):
                errors.append(
                    f"{gene}: parent {parent} does not list {gene} in children (registered genomes only)"
                )
        for child in lineage.get("children") or []:
            if child in registered and gene not in (genomes[child].get("lineage") or {}).get("parents", []):
                errors.append(
                    f"{gene}: child {child} does not list {gene} in parents (registered genomes only)"
                )
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    genome_dir = root / GENOME_DIR
    meta_path = root / META_SCHEMA

    if not meta_path.is_file():
        print(f"[genome-gate] FAIL: meta-schema missing: {meta_path}")
        return 1

    try:
        load_json(meta_path)
    except json.JSONDecodeError as exc:
        print(f"[genome-gate] FAIL: invalid meta-schema: {exc}")
        return 1

    files = sorted(genome_dir.glob("*.genome.v1.json"))
    if not files:
        print("[genome-gate] FAIL: no genome files in registry")
        return 1

    print(f"[genome-gate] checking {len(files)} genome(s)")
    all_errors: list[str] = []
    parsed: dict[str, dict[str, Any]] = {}

    for path in files:
        try:
            data = load_json(path)
        except json.JSONDecodeError as exc:
            all_errors.append(f"{path.name}: invalid JSON: {exc}")
            continue
        if not isinstance(data, dict):
            all_errors.append(f"{path.name}: root must be object")
            continue
        gene = (data.get("identity") or {}).get("gene")
        if isinstance(gene, str):
            parsed[gene] = data
        all_errors.extend(validate_genome(data, path, root))

    all_errors.extend(validate_lineage_symmetry(parsed))

    if all_errors:
        for err in all_errors:
            print(f"[genome-gate] FAIL: {err}")
        return 1

    print("[genome-gate] PASS: all subsystem genomes valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
