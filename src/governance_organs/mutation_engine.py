"""Mutation Engine (MP-X) — backward-compatible schema evolution with rollback."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._audit import append_audit
from src.governance_organs._paths import repo_root, runtime_governance_dir
from src.governance_organs.genome_engine import GenomeEngine, load_json

MP_FRONT_MATTER = re.compile(
    r"^---\s*\n(.*?)\n---",
    re.DOTALL | re.MULTILINE,
)


@dataclass
class MutationProposal:
    mp_id: str
    gene: str
    status: str
    backward_compatible: bool
    schema_delta_ref: str | None
    path: Path
    raw: dict[str, str] = field(default_factory=dict)


@dataclass
class MutationResult:
    mp_id: str
    gene: str
    passed: bool
    failures: list[str] = field(default_factory=list)


class MutationEngine:
    def __init__(self, root: Path | None = None):
        self.root = root or repo_root()
        self.mutations_dir = self.root / "docs/_future/mutations"
        self.deltas_dir = self.root / "schemas/deltas"

    def list_proposals(self, gene: str | None = None) -> list[MutationProposal]:
        proposals: list[MutationProposal] = []
        if not self.mutations_dir.is_dir():
            return proposals
        for path in sorted(self.mutations_dir.glob("MP-*.md")):
            proposal = self._parse_proposal(path)
            if proposal and (gene is None or proposal.gene == gene):
                proposals.append(proposal)
        return proposals

    def _parse_proposal(self, path: Path) -> MutationProposal | None:
        text = path.read_text(encoding="utf-8")
        mp_id = path.stem
        fields: dict[str, str] = {"mp_id": mp_id}
        match = MP_FRONT_MATTER.match(text)
        if match:
            for line in match.group(1).splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    fields[key.strip()] = value.strip()
        else:
            for line in text.splitlines():
                if line.startswith("- ") and ":" in line:
                    key, value = line[2:].split(":", 1)
                    fields[key.strip()] = value.strip()
        gene = fields.get("gene", "")
        if not gene:
            title_match = re.search(r"MP-[\w-]+:\s*(\w+)", text)
            if title_match:
                gene = title_match.group(1)
        status = fields.get("status", "proposed")
        backward = fields.get("backward_compatible", "true").lower() in {
            "true",
            "yes",
            "1",
        }
        return MutationProposal(
            mp_id=mp_id,
            gene=gene,
            status=status,
            backward_compatible=backward,
            schema_delta_ref=fields.get("schema_delta_ref"),
            path=path,
            raw=fields,
        )

    def _genome_path(self, gene: str) -> Path:
        return GenomeEngine.registry().paths[gene]

    def _backup_genome(self, gene: str) -> Path:
        backup_dir = runtime_governance_dir() / "mutation_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dest = backup_dir / f"{gene}_{stamp}.genome.v1.json"
        shutil.copy2(self._genome_path(gene), dest)
        return dest

    def verify(self, gene: str, mp_id: str) -> MutationResult:
        failures: list[str] = []
        proposal = next(
            (p for p in self.list_proposals(gene) if p.mp_id == mp_id),
            None,
        )
        if proposal is None:
            return MutationResult(mp_id=mp_id, gene=gene, passed=False, failures=["proposal not found"])
        if not proposal.backward_compatible:
            failures.append("backward_compatible must be true")
        if proposal.schema_delta_ref:
            delta_path = self.root / proposal.schema_delta_ref
            if not delta_path.is_file():
                failures.append(f"schema delta missing: {proposal.schema_delta_ref}")
        import sys

        script = self.root / "tools/governance/check_subsystem_genome.py"
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        if proc.returncode != 0:
            failures.append("genome-gate failed during mutation verify")
        test_path = self.root / "tests" / f"test_{gene}_mutation_{mp_id.replace('-', '_')}.py"
        if not test_path.is_file():
            alt = self.root / "tests" / f"test_{gene}_mutation.py"
            if not alt.is_file():
                failures.append("mutation tests missing")
        return MutationResult(mp_id=mp_id, gene=gene, passed=not failures, failures=failures)

    def apply(self, gene: str, mp_id: str, *, invariant: str | None = None) -> MutationResult:
        result = self.verify(gene, mp_id)
        if not result.passed:
            return result
        proposal = next(p for p in self.list_proposals(gene) if p.mp_id == mp_id)
        backup = self._backup_genome(gene)
        path = self._genome_path(gene)
        data = load_json(path)
        gov = data.setdefault("governance", {})
        invariants = list(gov.get("invariants") or [])
        if invariant and invariant not in invariants:
            invariants.append(invariant)
            gov["invariants"] = invariants
        history = data.setdefault("mutation", {}).setdefault("history", [])
        history.append(
            {
                "proposal_id": mp_id,
                "status": "promoted",
                "schema_delta_ref": proposal.schema_delta_ref,
                "notes": f"backup: {backup.relative_to(self.root)}",
            }
        )
        version = str((data.get("identity") or {}).get("version") or "1.0.0")
        if version.count(".") >= 2:
            parts = version.split("-")[0].split(".")
            parts[-1] = str(int(parts[-1]) + 1) if parts[-1].isdigit() else "1"
            data.setdefault("identity", {})["version"] = ".".join(parts[:3])
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        GenomeEngine.reload(self.root)
        append_audit(
            "mutation_audit.jsonl",
            {"action": "mutation_apply", "gene": gene, "mp_id": mp_id, "backup": str(backup)},
        )
        return result

    def rollback(self, gene: str, mp_id: str) -> bool:
        backup_dir = runtime_governance_dir() / "mutation_backups"
        backups = sorted(backup_dir.glob(f"{gene}_*.genome.v1.json"))
        if not backups:
            return False
        shutil.copy2(backups[-1], self._genome_path(gene))
        data = load_json(self._genome_path(gene))
        history = data.get("mutation", {}).get("history") or []
        for entry in reversed(history):
            entry_id = entry.get("proposal_id") or entry.get("mp_id")
            if entry_id == mp_id and entry.get("status") == "promoted":
                entry["status"] = "reverted"
                break
        self._genome_path(gene).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        GenomeEngine.reload(self.root)
        append_audit(
            "mutation_audit.jsonl",
            {"action": "mutation_rollback", "gene": gene, "mp_id": mp_id},
        )
        return True


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Alt-4 Mutation Engine")
    parser.add_argument("--gene", required=True)
    parser.add_argument("--mp-id", required=True)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    parser.add_argument("--invariant", help="Invariant to append on apply")
    args = parser.parse_args()

    engine = MutationEngine()
    if args.rollback:
        ok = engine.rollback(args.gene, args.mp_id)
        return 0 if ok else 1
    if args.apply:
        result = engine.apply(args.gene, args.mp_id, invariant=args.invariant)
    else:
        result = engine.verify(args.gene, args.mp_id)
    print(json.dumps(result.__dict__, indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":
    import sys
    from pathlib import Path

    _root = Path(__file__).resolve().parents[2]
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    raise SystemExit(main())
