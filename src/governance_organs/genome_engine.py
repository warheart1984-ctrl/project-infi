"""Genome Engine — DNA validation on boot, gates, and subsystem calls."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root

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

STAGE_RANK = {
    "concept": 0,
    "prototype": 1,
    "mvp": 2,
    "governed": 3,
    "deprecated": -1,
    "retired": -2,
}

CALLABLE_STAGES = frozenset({"mvp", "governed"})

# capability_id / module path fragments → registry gene
GENE_ALIASES: dict[str, str] = {
    "recipe": "recipe_module_organ",
    "recipe_module": "recipe_module_organ",
    "recipe_module_organ": "recipe_module_organ",
    "imagine": "imagine_generator",
    "imagine_generator": "imagine_generator",
    "human_voice": "human_voice_extraction",
    "human_voice_extraction": "human_voice_extraction",
    "narrative": "narrative_trust_pack",
    "narrative_trust_pack": "narrative_trust_pack",
    "triangulation": "forensic_triangulation",
    "forensic_triangulation": "forensic_triangulation",
    "lineage": "cisiv_operator_lineage_console",
    "cisiv_operator_lineage_console": "cisiv_operator_lineage_console",
    "cisiv": "cisiv_operator_lineage_console",
    "safety_envelope": "safety_envelope_organ",
    "safety_envelope_organ": "safety_envelope_organ",
    "operator_profile": "operator_profile_organ",
    "operator_profile_organ": "operator_profile_organ",
    "reflection_runtime": "reflection_runtime_organ",
    "reflection_runtime_organ": "reflection_runtime_organ",
    "memory_runtime": "memory_runtime_organ",
    "memory_runtime_organ": "memory_runtime_organ",
}


class GenomeValidationError(Exception):
    """Raised when subsystem DNA fails validation or call policy."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or [message]


@dataclass
class GenomeRegistry:
    root: Path
    genomes: dict[str, dict[str, Any]] = field(default_factory=dict)
    paths: dict[str, Path] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    mtimes: dict[str, float] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


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
    invariants = gov.get("invariants") or []
    for i, entry in enumerate(invariants):
        if isinstance(entry, str):
            continue
        if isinstance(entry, dict) and entry.get("text") and entry.get("maturity") in {
            "emergent",
            "stable",
            "constitutional",
        }:
            continue
        errors.append(f"{gene_file}: governance.invariants[{i}] invalid Tier5 entry")
    lanes = gov.get("operator_lanes")
    if lanes is not None:
        if not isinstance(lanes, list):
            errors.append(f"{gene_file}: governance.operator_lanes must be array")
        else:
            for i, lane in enumerate(lanes):
                if not isinstance(lane, dict) or not lane.get("lane_id"):
                    errors.append(f"{gene_file}: governance.operator_lanes[{i}] invalid")
    gates = gov.get("contextual_gates")
    if gates is not None:
        if not isinstance(gates, list):
            errors.append(f"{gene_file}: governance.contextual_gates must be array")
        else:
            for i, gate in enumerate(gates):
                if not isinstance(gate, dict) or not gate.get("gate_id"):
                    errors.append(f"{gene_file}: governance.contextual_gates[{i}] invalid")
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
    if stage == "prototype":
        for i, entry in enumerate(surface):
            if isinstance(entry, dict) and entry.get("isolated") is not True:
                errors.append(
                    f"{gene_file}: prototype runtime.surface[{i}] must set isolated: true"
                )
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
            if parent in registered and gene not in (genomes[parent].get("lineage") or {}).get(
                "children", []
            ):
                errors.append(
                    f"{gene}: parent {parent} does not list {gene} in children (registered genomes only)"
                )
        for child in lineage.get("children") or []:
            if child in registered and gene not in (genomes[child].get("lineage") or {}).get(
                "parents", []
            ):
                errors.append(
                    f"{gene}: child {child} does not list {gene} in parents (registered genomes only)"
                )
    return errors


def load_registry(root: Path | None = None) -> GenomeRegistry:
    root = root or repo_root()
    genome_dir = root / GENOME_DIR
    meta_path = root / META_SCHEMA
    registry = GenomeRegistry(root=root)

    if not meta_path.is_file():
        registry.errors.append(f"meta-schema missing: {meta_path}")
        return registry

    try:
        load_json(meta_path)
    except json.JSONDecodeError as exc:
        registry.errors.append(f"invalid meta-schema: {exc}")
        return registry

    files = sorted(genome_dir.glob("*.genome.v1.json"))
    if not files:
        registry.errors.append("no genome files in registry")
        return registry

    parsed: dict[str, dict[str, Any]] = {}
    for path in files:
        try:
            data = load_json(path)
        except json.JSONDecodeError as exc:
            registry.errors.append(f"{path.name}: invalid JSON: {exc}")
            continue
        if not isinstance(data, dict):
            registry.errors.append(f"{path.name}: root must be object")
            continue
        gene = (data.get("identity") or {}).get("gene")
        if isinstance(gene, str):
            parsed[gene] = data
            registry.genomes[gene] = data
            registry.paths[gene] = path
            registry.mtimes[gene] = path.stat().st_mtime
        registry.errors.extend(validate_genome(data, path, root))

    registry.errors.extend(validate_lineage_symmetry(parsed))
    return registry


class GenomeEngine:
    """Runtime DNA validator with registry cache."""

    _registry: GenomeRegistry | None = None
    _root: Path | None = None

    @classmethod
    def root(cls) -> Path:
        if cls._root is None:
            cls._root = repo_root()
        return cls._root

    @classmethod
    def reload(cls, root: Path | None = None) -> GenomeRegistry:
        cls._root = root or repo_root()
        cls._registry = load_registry(cls._root)
        return cls._registry

    @classmethod
    def registry(cls) -> GenomeRegistry:
        if cls._registry is None:
            cls.reload()
        assert cls._registry is not None
        return cls._registry

    @classmethod
    def validate_registry(cls, root: Path | None = None) -> GenomeRegistry:
        reg = cls.reload(root)
        if not reg.ok:
            raise GenomeValidationError(
                "subsystem genome registry invalid",
                reg.errors,
            )
        return reg

    @classmethod
    def validate_registry_boot(cls) -> GenomeRegistry:
        mode = __import__("os").getenv("AAIS_GENOME_BOOT", "fail").strip().lower()
        reg = cls.reload()
        if reg.ok:
            return reg
        if mode in {"warn", "warning", "skip"}:
            return reg
        raise GenomeValidationError(
            "genome boot validation failed",
            reg.errors,
        )

    @classmethod
    def resolve_gene(cls, hint: str | None) -> str | None:
        if not hint:
            return None
        normalized = hint.replace("-", "_").strip().lower()
        if normalized in cls.registry().genomes:
            return normalized
        if normalized in GENE_ALIASES:
            return GENE_ALIASES[normalized]
        for gene, data in cls.registry().genomes.items():
            if normalized == gene or normalized in gene.split("_"):
                return gene
            for entry in (data.get("runtime") or {}).get("surface") or []:
                path = str((entry or {}).get("path") or "").lower()
                if normalized in path:
                    return gene
        return GENE_ALIASES.get(normalized)

    @classmethod
    def assert_gene_callable(cls, gene: str | None, *, stage_min: str = "mvp") -> None:
        if not gene:
            return
        reg = cls.registry()
        data = reg.genomes.get(gene)
        if data is None:
            return
        stage = (data.get("identity") or {}).get("stage", "")
        if stage in ("deprecated", "retired"):
            raise GenomeValidationError(
                f"subsystem {gene} is {stage}; integration calls blocked"
            )
        min_rank = STAGE_RANK.get(stage_min, 2)
        if STAGE_RANK.get(stage, -99) < min_rank:
            raise GenomeValidationError(
                f"subsystem {gene} stage {stage} below required {stage_min}"
            )
        if stage not in CALLABLE_STAGES and stage_min == "mvp":
            raise GenomeValidationError(
                f"subsystem {gene} stage {stage} not callable at runtime"
            )

    @classmethod
    def gate_main(cls) -> int:
        reg = cls.reload()
        if not reg.ok:
            for err in reg.errors:
                print(f"[genome-gate] FAIL: {err}")
            return 1
        print(f"[genome-gate] PASS: {len(reg.genomes)} genome(s) valid")
        return 0
