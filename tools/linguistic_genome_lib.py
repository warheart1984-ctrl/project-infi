#!/usr/bin/env python3
"""Shared library for linguistic genome validation, snapshots, and diffs."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ALIASES_PATH = ROOT / "governance" / "legacy_engineering_aliases.v1.json"
GENOME_DIR = ROOT / "governance" / "subsystem_genomes"
SNAPSHOT_DIR = ROOT / "governance" / "linguistic_snapshots"

LEGACY_SUFFIXES = ("_organ.py", "_fabric.py")
ENGINEERING_CLASS_PATTERN = re.compile(
    r"^[A-Z][a-zA-Z0-9]*([A-Z][a-zA-Z0-9]*)+$"
)
MYTHIC_FORBIDDEN_IN_GENE = frozenset({"summon", "wave", "fabric", "organ"})

HEADER_PATTERNS = {
    "mythic": re.compile(r"^#\s*Mythic:\s*(.+)$", re.MULTILINE),
    "engineering": re.compile(r"^#\s*Engineering:\s*(.+)$", re.MULTILINE),
    "responsibilities": re.compile(r"^#\s*Responsibilities:\s*(.+)$", re.MULTILINE),
    "non_responsibilities": re.compile(
        r"^#\s*Non-responsibilities:\s*(.+)$", re.MULTILINE
    ),
    "invariants": re.compile(r"^#\s*Invariants:\s*(.+)$", re.MULTILINE),
}

DOC_MYTHIC = re.compile(r"\*\*Mythic:\*\*\s*(.+?)(?:\n|$)", re.IGNORECASE)
DOC_ENGINEERING = re.compile(
    r"\*\*Engineering:\*\*\s*`?([^`\n]+)`?\s*(?:—|-)?\s*(.*?)(?:\n|$)",
    re.IGNORECASE,
)


@dataclass
class LinguisticRecord:
    gene: str
    genome_stage: str = ""
    layers: dict[str, Any] = field(default_factory=dict)
    fingerprints: dict[str, str] = field(default_factory=dict)

    def to_snapshot(
        self,
        capture_source: str = "naming-genome-gate",
    ) -> dict[str, Any]:
        return {
            "linguistic_snapshot_version": "linguistic_snapshot.v1",
            "gene": self.gene,
            "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "capture_source": capture_source,
            "genome_stage": self.genome_stage or None,
            "layers": self.layers,
            "fingerprints": self.fingerprints,
        }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_aliases(root: Path | None = None) -> dict[str, dict[str, Any]]:
    path = (root or ROOT) / "governance" / "legacy_engineering_aliases.v1.json"
    if not path.is_file():
        return {}
    data = load_json(path)
    return {e["gene"]: e for e in data.get("aliases", []) if e.get("gene")}


def load_grandfather_paths(root: Path | None = None) -> set[str]:
    aliases = load_aliases(root)
    paths: set[str] = set()
    for entry in aliases.values():
        legacy = entry.get("legacy_path")
        if legacy:
            paths.add(legacy.replace("\\", "/"))
    return paths


def is_grandfathered_gene(gene: str, aliases: dict[str, dict[str, Any]] | None = None) -> bool:
    aliases = aliases or load_aliases()
    if gene in aliases:
        return True
    return gene.endswith("_organ") or gene.endswith("_fabric")


def is_grandfathered_module(rel_path: str, gene: str, grandfather_paths: set[str]) -> bool:
    rel = rel_path.replace("\\", "/")
    if rel in grandfather_paths:
        return True
    if is_grandfathered_gene(gene):
        if rel.endswith("_organ.py") or rel.endswith("_fabric.py"):
            return True
        if rel == f"src/{gene}.py":
            return True
    return False


def validate_engineering_class(name: str) -> bool:
    if not name or not ENGINEERING_CLASS_PATTERN.match(name):
        return False
    return True


def derive_engineering_class(gene: str) -> tuple[str, str]:
    """Heuristic PascalCase class + mythic label from snake_case gene."""
    s = gene
    mythic = gene.replace("_", " ").title()
    if s.endswith("_fabric"):
        s, role = s[:-7], "Layer"
        if "coherence" in gene:
            mythic = "Coherence Fabric"
    elif s.endswith("_organ"):
        s, role = s[:-6], "Engine"
        if "bridge" in gene or "handoff" in gene:
            role = "Bridge"
        elif "gate" in gene or "sentinel" in gene:
            role = "Monitor" if "monitor" in gene else "Gate"
        elif "projection" in gene:
            role = "Layer"
        elif any(
            x in gene
            for x in ("lane", "route", "surface", "console", "interface")
        ):
            role = "Interface"
        else:
            role = "Engine"
    elif s.endswith("_lane"):
        s, role = s[:-5], "Lane"
    else:
        role = "Engine"
    parts = [p for p in s.split("_") if p]
    base = "".join(p[:1].upper() + p[1:] for p in parts)
    return base + role, mythic


# Manual overrides for non-organ genes without alias entries
GENE_OVERRIDES: dict[str, tuple[str, str]] = {
    "cisiv_operator_lineage_console": (
        "UlLineageEngine",
        "Ul Lineage",
    ),
    "forensic_triangulation": (
        "ForensicTriangulationEngine",
        "Forensic triangulation ledger",
    ),
    "narrative_trust_pack": ("NarrativeTrustPackEngine", "Narrative trust pack"),
    "recipe_module": ("RecipeModuleEngine", "Recipe module"),
    "imagine_generator": ("ImagineGeneratorEngine", "Imagine generator"),
    "human_voice_extraction": (
        "HumanVoiceExtractionEngine",
        "Human voice extraction",
    ),
    "capability_service_bridge": (
        "CapabilityServiceBridge",
        "Capability service bridge",
    ),
    "jarvis_memory_board": ("JarvisMemoryBoard", "Jarvis memory board"),
    "operator_cognition_coherence_fabric": (
        "OperatorCognitionCoherenceLayer",
        "Coherence Fabric",
    ),
}


def resolve_linguistic_names(
    gene: str, aliases: dict[str, dict[str, Any]] | None = None
) -> tuple[str, str]:
    aliases = aliases or load_aliases()
    if gene in GENE_OVERRIDES:
        return GENE_OVERRIDES[gene]
    if gene in aliases:
        e = aliases[gene]
        return e.get("engineering_class", ""), e.get("mythic_label", "")
    return derive_engineering_class(gene)


def extract_source_layers(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    header: dict[str, str] = {}
    for key, pat in HEADER_PATTERNS.items():
        m = pat.search(text)
        if m:
            header[key] = m.group(1).strip()
    symbols: list[dict[str, str]] = []
    for block in re.finditer(
        r"(# Mythic:[^\n]+\n# Engineering:[^\n]+(?:\n# (?:Invariant|Boundary):[^\n]+)*)",
        text,
    ):
        lines = block.group(1).splitlines()
        sym: dict[str, str] = {"raw": block.group(1)[:200]}
        for line in lines:
            if line.startswith("# Mythic:"):
                sym["mythic"] = line.split(":", 1)[1].strip()
            elif line.startswith("# Engineering:"):
                sym["engineering"] = line.split(":", 1)[1].strip()
        if "mythic" in sym or "engineering" in sym:
            symbols.append(sym)
    return {
        "path": path.as_posix(),
        "header": header,
        "symbols": symbols,
    }


def extract_doc_layers(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    out: dict[str, str] = {}
    m_m = DOC_MYTHIC.search(text)
    if m_m:
        out["mythic"] = m_m.group(1).strip()
    m_e = DOC_ENGINEERING.search(text)
    if m_e:
        cls = m_e.group(1).strip()
        detail = (m_e.group(2) or "").strip()
        out["engineering_class"] = cls
        if detail:
            out["engineering_detail"] = detail
    title = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if title:
        out["title"] = title.group(1).strip()
    return out


def extract_genome_layers(genome: dict[str, Any]) -> dict[str, Any]:
    identity = genome.get("identity") or {}
    ssp = genome.get("ssp") or {}
    module_path = ""
    for entry in (genome.get("runtime") or {}).get("surface") or []:
        if isinstance(entry, dict) and entry.get("kind") == "module":
            module_path = entry.get("path") or ""
            break
    return {
        "gene": identity.get("gene", ""),
        "engineering_class": ssp.get("engineering_class", ""),
        "mythic_label": ssp.get("mythic_label", ""),
        "linguistic_version": ssp.get("linguistic_version", ""),
        "display_name": identity.get("display_name", ""),
        "module_path": module_path,
    }


def _fingerprint_text(*parts: str) -> str:
    payload = "\n".join(p.strip() for p in parts if p).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compute_fingerprints(layers: dict[str, Any]) -> dict[str, str]:
    genome = layers.get("genome") or {}
    source = layers.get("source") or {}
    docs = layers.get("docs") or {}
    mythic_parts = [
        genome.get("mythic_label", ""),
        (source.get("header") or {}).get("mythic", ""),
        (docs.get("concept_spec") or {}).get("mythic", ""),
        (docs.get("active_doc") or {}).get("mythic", ""),
    ]
    eng_parts = [
        genome.get("engineering_class", ""),
        (source.get("header") or {}).get("engineering", ""),
        (docs.get("concept_spec") or {}).get("engineering_class", ""),
    ]
    mythic_fp = _fingerprint_text(*mythic_parts)
    eng_fp = _fingerprint_text(*eng_parts)
    combined = _fingerprint_text(mythic_fp, eng_fp)
    return {"mythic": mythic_fp, "engineering": eng_fp, "combined": combined}


def load_genome(gene: str, root: Path | None = None) -> dict[str, Any] | None:
    root = root or ROOT
    gdir = root / "governance" / "subsystem_genomes"
    genomes = list(gdir.glob("*.genome.v1.json"))
    for path in genomes:
        data = load_json(path)
        if (data.get("identity") or {}).get("gene") == gene:
            return data
    return None


def genome_path_for_gene(gene: str, root: Path | None = None) -> Path | None:
    root = root or ROOT
    gdir = root / "governance" / "subsystem_genomes"
    for path in gdir.glob("*.genome.v1.json"):
        data = load_json(path)
        if (data.get("identity") or {}).get("gene") == gene:
            return path
    return None


def list_all_genes(root: Path | None = None) -> list[str]:
    root = root or ROOT
    genes: list[str] = []
    gdir = root / "governance" / "subsystem_genomes"
    for path in sorted(gdir.glob("*.genome.v1.json")):
        data = load_json(path)
        gene = (data.get("identity") or {}).get("gene")
        if gene:
            genes.append(gene)
    return genes


def build_linguistic_record(gene: str, root: Path | None = None) -> LinguisticRecord | None:
    root = root or ROOT
    genome = load_genome(gene, root)
    if not genome:
        return None
    identity = genome.get("identity") or {}
    ssp = genome.get("ssp") or {}
    genome_layer = extract_genome_layers(genome)

    source_layer: dict[str, Any] = {}
    mod = genome_layer.get("module_path")
    if mod:
        src_path = root / mod
        source_layer = extract_source_layers(src_path)

    docs_layer: dict[str, Any] = {}
    cs = ssp.get("concept_spec")
    if cs:
        docs_layer["concept_spec"] = extract_doc_layers(root / cs)
    ad = ssp.get("active_doc")
    if ad:
        docs_layer["active_doc"] = extract_doc_layers(root / ad)

    layers = {
        "genome": genome_layer,
        "source": source_layer or None,
        "docs": docs_layer or None,
    }
    layers = {k: v for k, v in layers.items() if v}
    fps = compute_fingerprints(layers)
    return LinguisticRecord(
        gene=gene,
        genome_stage=identity.get("stage", ""),
        layers=layers,
        fingerprints=fps,
    )


def list_snapshots(gene: str, root: Path | None = None) -> list[Path]:
    root = root or ROOT
    snap_dir = root / "governance" / "linguistic_snapshots" / gene
    if not snap_dir.is_dir():
        return []
    return sorted(snap_dir.glob("*.json"))


def load_snapshot(path: Path) -> dict[str, Any]:
    return load_json(path)


def latest_snapshot(gene: str, root: Path | None = None) -> dict[str, Any] | None:
    snaps = list_snapshots(gene, root)
    if not snaps:
        return None
    return load_snapshot(snaps[-1])


def write_snapshot(
    record: LinguisticRecord,
    root: Path | None = None,
    capture_source: str = "naming-genome-gate",
    force: bool = False,
) -> Path | None:
    root = root or ROOT
    latest = latest_snapshot(record.gene, root)
    if latest and not force:
        if latest.get("fingerprints", {}).get("combined") == record.fingerprints.get(
            "combined"
        ):
            return None
    snap_dir = root / "governance" / "linguistic_snapshots" / record.gene
    snap_dir.mkdir(parents=True, exist_ok=True)
    payload = record.to_snapshot(capture_source=capture_source)
    ts = payload["captured_at"].replace(":", "").replace("-", "")
    out = snap_dir / f"{ts}.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out


@dataclass
class FieldChange:
    layer: str
    field: str
    before: str
    after: str


@dataclass
class LinguisticDiff:
    gene: str
    from_source: str
    to_source: str
    captured_at: str
    changes: list[FieldChange] = field(default_factory=list)


def _layer_mythic(layers: dict[str, Any]) -> str:
    g = layers.get("genome") or {}
    parts = [g.get("mythic_label", "")]
    src = layers.get("source") or {}
    parts.append((src.get("header") or {}).get("mythic", ""))
    docs = layers.get("docs") or {}
    parts.append((docs.get("concept_spec") or {}).get("mythic", ""))
    return " | ".join(p for p in parts if p) or "(none)"


def _layer_engineering(layers: dict[str, Any]) -> str:
    g = layers.get("genome") or {}
    return g.get("engineering_class", "") or "(none)"


def _layer_invariants(layers: dict[str, Any]) -> str:
    src = layers.get("source") or {}
    inv = (src.get("header") or {}).get("invariants", "")
    g = layers.get("genome") or {}
    return inv or g.get("linguistic_version", "") or "(none)"


def diff_records(
    old: dict[str, Any], new: dict[str, Any]
) -> LinguisticDiff:
    gene = new.get("gene") or old.get("gene") or ""
    old_layers = old.get("layers") or {}
    new_layers = new.get("layers") or {}
    changes: list[FieldChange] = []

    pairs = [
        ("combined", "Mythic", _layer_mythic(old_layers), _layer_mythic(new_layers)),
        (
            "combined",
            "Engineering",
            _layer_engineering(old_layers),
            _layer_engineering(new_layers),
        ),
        (
            "combined",
            "Invariants",
            _layer_invariants(old_layers),
            _layer_invariants(new_layers),
        ),
    ]
    for _layer_name, field_name, before, after in pairs:
        if before != after:
            changes.append(
                FieldChange(
                    layer="linguistic",
                    field=field_name,
                    before=before,
                    after=after,
                )
            )

    return LinguisticDiff(
        gene=gene,
        from_source=old.get("capture_source", "unknown"),
        to_source=new.get("capture_source", "unknown"),
        captured_at=new.get("captured_at", ""),
        changes=changes,
    )


def format_diff_markdown(diffs: list[LinguisticDiff], gene: str) -> str:
    lines = [f"# Linguistic diff — `{gene}`", ""]
    if not diffs:
        lines.append("_No linguistic transitions detected._")
        return "\n".join(lines) + "\n"
    for d in diffs:
        if not d.changes:
            continue
        lines.append(f"## {d.captured_at} — {d.to_source}")
        lines.append("")
        lines.append(f"Provenance: `{d.from_source}` → `{d.to_source}`")
        lines.append("")
        lines.append("| Layer | Before | After |")
        lines.append("|-------|--------|-------|")
        for c in d.changes:
            b = c.before.replace("|", "\\|")
            a = c.after.replace("|", "\\|")
            lines.append(f"| {c.field} | {b} | {a} |")
        lines.append("")
    return "\n".join(lines)


def genome_linked_paths(gene: str, root: Path | None = None) -> list[str]:
    root = root or ROOT
    genome = load_genome(gene, root)
    if not genome:
        return []
    paths: list[str] = []
    gpath = genome_path_for_gene(gene, root)
    if gpath:
        paths.append(gpath.relative_to(root).as_posix())
    ssp = genome.get("ssp") or {}
    for key in ("concept_spec", "mvp_plan", "active_doc"):
        p = ssp.get(key)
        if p:
            paths.append(p)
    for entry in (genome.get("runtime") or {}).get("surface") or []:
        if isinstance(entry, dict) and entry.get("path"):
            p = entry["path"]
            if p.endswith(".py"):
                paths.append(p)
    return list(dict.fromkeys(paths))
