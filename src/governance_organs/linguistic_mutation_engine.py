"""Linguistic Mutation Engine — MP-X linguistic_layer apply/rollback."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root, runtime_governance_dir
from src.governance_organs.genome_engine import GenomeEngine, load_json
from tools.linguistic_genome_lib import genome_path_for_gene

ENGINEERING_CLASS_PATTERN = re.compile(
    r"^[A-Z][a-zA-Z0-9]*([A-Z][a-zA-Z0-9]*)+$"
)


def validate_engineering_class(name: str) -> bool:
    return bool(name and ENGINEERING_CLASS_PATTERN.match(name))


def _linguistic_delta_path(root: Path, gene: str, mp_id: str) -> Path:
    return root / "schemas/deltas" / f"{gene}_{mp_id}_linguistic.json"


def validate_linguistic_delta(
    delta: dict[str, Any],
    genome: dict[str, Any],
    aliases: dict[str, dict[str, Any]],
) -> list[str]:
    failures: list[str] = []
    if delta.get("mutation_kind") != "linguistic_layer":
        failures.append("mutation_kind must be linguistic_layer")
    if delta.get("backward_compatible") is not True:
        failures.append("backward_compatible must be true")
    gene = (genome.get("identity") or {}).get("gene", "")
    if delta.get("gene") != gene:
        failures.append(f"delta gene {delta.get('gene')!r} != genome gene {gene!r}")

    after = delta.get("after") or {}
    eng = after.get("engineering_class", "")
    if not validate_engineering_class(eng):
        failures.append(f"invalid after.engineering_class: {eng!r}")

    before = delta.get("before") or {}
    ssp = genome.get("ssp") or {}
    if before.get("engineering_class") and before.get("engineering_class") != ssp.get(
        "engineering_class"
    ):
        failures.append("before.engineering_class does not match current genome ssp")
    if before.get("mythic_label") and before.get("mythic_label") != ssp.get("mythic_label"):
        failures.append("before.mythic_label does not match current genome ssp")

    if gene in aliases:
        expected = aliases[gene].get("engineering_class", "")
        if eng and expected and eng != expected and not delta.get("alias_override_justification"):
            failures.append(
                f"after.engineering_class {eng!r} != alias {expected!r} "
                "(requires alias_override_justification)"
            )

    if not delta.get("bump_linguistic_version"):
        failures.append("bump_linguistic_version required")

    from src.governance_organs.linguistic_cascade_engine import validate_cascade_ack

    failures.extend(validate_cascade_ack(delta, Path(__file__).resolve().parents[2]))

    return failures


def _touch_source_header(root: Path, genome: dict[str, Any], after: dict[str, str]) -> None:
    module_path = ""
    for entry in (genome.get("runtime") or {}).get("surface") or []:
        if isinstance(entry, dict) and entry.get("kind") == "module":
            module_path = entry.get("path") or ""
            break
    if not module_path:
        return
    path = root / module_path
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if "# Engineering:" in text:
        return
    header = (
        f"# Mythic: {after.get('mythic_label', '')}\n"
        f"# Engineering: {after.get('engineering_class', '')}\n"
        f"# Responsibilities: (Wave 2 header via MP-LING)\n"
        f"# Non-responsibilities: TBD\n"
        f"# Invariants: TBD\n\n"
    )
    if text.startswith('"""'):
        end = text.find('"""', 3)
        if end != -1:
            insert_at = end + 3
            if text[insert_at : insert_at + 1] == "\n":
                insert_at += 1
            text = text[:insert_at] + "\n" + header + text[insert_at:]
        else:
            text = header + text
    else:
        text = header + text
    path.write_text(text, encoding="utf-8")


def apply_linguistic_mutation(
    mp_id: str,
    gene: str,
    root: Path | None = None,
    *,
    dry_run: bool = False,
) -> tuple[bool, list[str]]:
    root = root or repo_root()
    delta_path = _linguistic_delta_path(root, gene, mp_id)
    if not delta_path.is_file():
        return False, [f"linguistic delta missing: {delta_path.relative_to(root)}"]

    from tools.linguistic_genome_lib import genome_path_for_gene, load_aliases

    aliases = load_aliases(root)
    genome_path = genome_path_for_gene(gene, root)
    if not genome_path:
        return False, [f"genome not found for gene {gene!r}"]
    data = load_json(genome_path)
    delta = load_json(delta_path)
    failures = validate_linguistic_delta(delta, data, aliases)
    if failures:
        return False, failures

    from src.governance_organs.linguistic_cascade_engine import cascade_impact

    before = delta.get("before") or {}
    after = delta.get("after") or {}
    impact = cascade_impact(gene, {"genome": before}, {"genome": after}, root)
    cascade_warnings: list[str] = []
    if impact.parent_changed and impact.children:
        high = [c.gene for c in impact.children if c.drift_band == "high"]
        if high:
            cascade_warnings.append(
                f"cascade preview: high-drift children: {', '.join(high[:5])}"
                + ("..." if len(high) > 5 else "")
            )

    if dry_run:
        return True, cascade_warnings

    backup_dir = runtime_governance_dir() / "mutation_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = backup_dir / f"{gene}_{stamp}.genome.v1.json"
    shutil.copy2(genome_path, backup)

    after = delta.get("after") or {}
    ssp = data.setdefault("ssp", {})
    if after.get("mythic_label"):
        ssp["mythic_label"] = after["mythic_label"]
    if after.get("engineering_class"):
        ssp["engineering_class"] = after["engineering_class"]
    ssp["linguistic_version"] = delta.get("bump_linguistic_version")

    history = data.setdefault("mutation", {}).setdefault("history", [])
    history.append(
        {
            "proposal_id": mp_id,
            "status": "promoted",
            "schema_delta_ref": str(delta_path.relative_to(root)).replace("\\", "/"),
            "notes": f"linguistic_layer backup: {backup.relative_to(root)}",
        }
    )
    genome_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    GenomeEngine.reload(root)

    if delta.get("touch_source_header"):
        _touch_source_header(root, data, after)

    return True, cascade_warnings


def rollback_linguistic_mutation(mp_id: str, gene: str, root: Path | None = None) -> bool:
    root = root or repo_root()
    backup_dir = runtime_governance_dir() / "mutation_backups"
    backups = sorted(backup_dir.glob(f"{gene}_*.genome.v1.json"))
    if not backups:
        return False
    genome_path = genome_path_for_gene(gene, root)
    if not genome_path:
        return False
    shutil.copy2(backups[-1], genome_path)
    data = load_json(genome_path)
    history = data.get("mutation", {}).get("history") or []
    for entry in reversed(history):
        if entry.get("proposal_id") == mp_id and entry.get("status") == "promoted":
            entry["status"] = "reverted"
            break
    genome_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    GenomeEngine.reload(root)
    return True
