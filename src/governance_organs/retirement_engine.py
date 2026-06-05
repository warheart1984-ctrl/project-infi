"""Retirement Engine — 10-step safe subsystem shutdown with lineage preservation."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._audit import append_audit
from src.governance_organs._paths import repo_root, runtime_governance_dir
from src.governance_organs.genome_engine import GenomeEngine, load_json

RETIREMENT_STEPS = (
    "mark_deprecated_in_spec",
    "freeze_schema",
    "freeze_api_doc",
    "logbook_entry",
    "move_docs_to_retired",
    "genome_deprecated",
    "summon_ineligible",
    "activation_order_removed",
    "shim_optional",
    "code_removal_gated",
)

EMISSION_RELEASES = 2
API_FREEZE_MARKER = "## API Freeze (Retirement)"


@dataclass
class RetirementState:
    gene: str
    current_step: int = 0
    completed_steps: list[str] = field(default_factory=list)
    dry_run: bool = True
    failures: list[str] = field(default_factory=list)
    notes: dict[str, Any] = field(default_factory=dict)


class RetirementEngine:
    def __init__(self, root: Path | None = None):
        self.root = root or repo_root()
        self.state_dir = runtime_governance_dir() / "retirement"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.emission_dir = runtime_governance_dir() / "emission"
        self.emission_dir.mkdir(parents=True, exist_ok=True)
        self.retired_docs = self.root / "docs/_retired"

    def _state_path(self, gene: str) -> Path:
        return self.state_dir / f"{gene}.json"

    def _emission_path(self, gene: str) -> Path:
        return self.emission_dir / f"{gene}.json"

    def load_state(self, gene: str) -> RetirementState:
        path = self._state_path(gene)
        if not path.is_file():
            return RetirementState(gene=gene)
        data = json.loads(path.read_text(encoding="utf-8"))
        return RetirementState(
            gene=gene,
            current_step=int(data.get("current_step", 0)),
            completed_steps=list(data.get("completed_steps") or []),
            dry_run=bool(data.get("dry_run", True)),
            failures=list(data.get("failures") or []),
            notes=dict(data.get("notes") or {}),
        )

    def save_state(self, state: RetirementState) -> None:
        self._state_path(state.gene).write_text(
            json.dumps(
                {
                    "gene": state.gene,
                    "current_step": state.current_step,
                    "completed_steps": state.completed_steps,
                    "dry_run": state.dry_run,
                    "failures": state.failures,
                    "notes": state.notes,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def _lineage_blocks_retirement(self, gene: str) -> list[str]:
        failures: list[str] = []
        for other_gene, data in GenomeEngine.registry().genomes.items():
            parents = (data.get("lineage") or {}).get("parents") or []
            if gene in parents:
                migration = (data.get("retirement") or {}).get("migration_proof")
                if not migration:
                    failures.append(
                        f"dependent {other_gene} lists {gene} as parent without migration_proof"
                    )
        return failures

    def _changelog_release_count(self) -> int:
        changelog = self.root / "CHANGELOG.md"
        if not changelog.is_file():
            return 0
        return len(re.findall(r"^## \[", changelog.read_text(encoding="utf-8"), re.MULTILINE))

    def _gene_activity_mtime(self, gene: str, data: dict[str, Any]) -> float | None:
        mtimes: list[float] = []
        runtime_root = self.root / ".runtime"
        if runtime_root.is_dir():
            try:
                for path in runtime_root.rglob("*"):
                    try:
                        if path.is_file() and gene in path.name:
                            mtimes.append(path.stat().st_mtime)
                    except OSError:
                        continue
            except OSError:
                pass
        for entry in (data.get("runtime") or {}).get("surface") or []:
            if not isinstance(entry, dict):
                continue
            rel = entry.get("path", "")
            if not rel or rel.startswith(("POST ", "GET ", "python ")):
                continue
            path = self.root / rel.split("#", 1)[0]
            if path.is_file():
                mtimes.append(path.stat().st_mtime)
        return max(mtimes) if mtimes else None

    def emission_unused(self, gene: str) -> dict[str, Any]:
        """Flag genes with no runtime activity across two stable release windows."""
        reg = GenomeEngine.registry()
        if gene not in reg.genomes:
            return {"unused": False, "reason": "unknown gene"}

        data = reg.genomes[gene]
        release_count = self._changelog_release_count()
        activity_mtime = self._gene_activity_mtime(gene, data)
        emission_path = self._emission_path(gene)
        prior: dict[str, Any] = {}
        if emission_path.is_file():
            prior = json.loads(emission_path.read_text(encoding="utf-8"))

        prior_release_count = int(prior.get("release_count_at_activity", release_count))
        prior_mtime = prior.get("activity_mtime")

        if activity_mtime is not None:
            if prior_mtime != activity_mtime:
                prior_release_count = release_count
            emission_path.write_text(
                json.dumps(
                    {
                        "gene": gene,
                        "activity_mtime": activity_mtime,
                        "release_count_at_activity": prior_release_count,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

        releases_since = max(0, release_count - prior_release_count)
        unused = activity_mtime is None or releases_since >= EMISSION_RELEASES
        return {
            "unused": unused,
            "activity_mtime": activity_mtime,
            "release_count": release_count,
            "releases_since_activity": releases_since,
            "releases_required": EMISSION_RELEASES,
        }

    def _mark_deprecated_in_spec(self, display: str) -> None:
        spec = self.root / "docs/runtime/AAIS_SUBSYSTEM_SPEC.md"
        text = spec.read_text(encoding="utf-8")
        pattern = re.compile(rf"\| {re.escape(display)} \| \w+ \|")
        if pattern.search(text):
            spec.write_text(
                pattern.sub(f"| {display} | deprecated |", text),
                encoding="utf-8",
            )

    def _freeze_api_doc(self, data: dict[str, Any]) -> None:
        active = (data.get("ssp") or {}).get("active_doc")
        if not active:
            return
        doc_path = self.root / active
        if not doc_path.is_file():
            return
        text = doc_path.read_text(encoding="utf-8")
        if API_FREEZE_MARKER in text:
            return
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        doc_path.write_text(
            text.rstrip()
            + f"\n\n{API_FREEZE_MARKER}\n\n"
            f"API frozen on {stamp} UTC per "
            f"[AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md]"
            f"(../../contracts/AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md).\n",
            encoding="utf-8",
        )

    def _apply_shim_optional(self, gene: str, path: Path) -> None:
        genome = load_json(path)
        retirement = genome.setdefault("retirement", {})
        successor = retirement.get("successor_gene")
        shim_required = bool(successor) or bool(retirement.get("shim_required"))
        retirement["shim_required"] = shim_required
        path.write_text(json.dumps(genome, indent=2) + "\n", encoding="utf-8")
        if shim_required:
            readme = self.retired_docs / gene / "README.md"
            readme.parent.mkdir(parents=True, exist_ok=True)
            if not readme.is_file():
                successor_note = (
                    f"Successor gene: `{successor}`." if successor else "No successor gene."
                )
                readme.write_text(
                    f"# {gene} — retirement shim\n\n"
                    f"{successor_note}\n\n"
                    f"Shim required per genome `retirement.shim_required`.\n",
                    encoding="utf-8",
                )

    def advance(
        self,
        gene: str,
        *,
        dry_run: bool = True,
        target_step: int = 6,
    ) -> RetirementState:
        state = self.load_state(gene)
        state.dry_run = dry_run
        state.failures = self._lineage_blocks_retirement(gene)
        if state.failures:
            self.save_state(state)
            return state

        reg = GenomeEngine.registry()
        if gene not in reg.genomes:
            state.failures.append(f"unknown gene: {gene}")
            self.save_state(state)
            return state

        data = reg.genomes[gene]
        display = (data.get("identity") or {}).get("display_name") or gene
        path = reg.paths[gene]

        while state.current_step < target_step and state.current_step < len(RETIREMENT_STEPS):
            step_name = RETIREMENT_STEPS[state.current_step]
            if step_name == "mark_deprecated_in_spec" and not dry_run:
                self._mark_deprecated_in_spec(display)
            elif step_name == "freeze_schema" and not dry_run:
                genome = load_json(path)
                genome.setdefault("schema", {})["frozen"] = True
                path.write_text(json.dumps(genome, indent=2) + "\n", encoding="utf-8")
            elif step_name == "freeze_api_doc" and not dry_run:
                self._freeze_api_doc(data)
            elif step_name == "logbook_entry" and not dry_run:
                logbook = self.root / "docs/audit/LOGBOOK.md"
                marker = f"### {display} — Retirement Started (Alt-4 Runtime)"
                if marker not in logbook.read_text(encoding="utf-8"):
                    logbook.write_text(
                        logbook.read_text(encoding="utf-8").rstrip()
                        + f"\n{marker}\n\n- CISIV stage: `verification`\n"
                        f"- scope: Retirement Engine step advance for `{gene}`\n",
                        encoding="utf-8",
                    )
            elif step_name == "move_docs_to_retired" and not dry_run:
                active = (data.get("ssp") or {}).get("active_doc")
                if active:
                    src = self.root / active
                    if src.is_file():
                        dest_dir = self.retired_docs / gene
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dest_dir / src.name)
            elif step_name == "genome_deprecated" and not dry_run:
                genome = load_json(path)
                genome.setdefault("identity", {})["stage"] = "deprecated"
                genome.setdefault("proof", {})["posture"] = "mvp"
                genome.setdefault("retirement", {})["path"] = (
                    f"docs/_retired/{gene}/README.md"
                )
                path.write_text(json.dumps(genome, indent=2) + "\n", encoding="utf-8")
                GenomeEngine.reload(self.root)
            elif step_name == "summon_ineligible" and not dry_run:
                genome = load_json(path)
                genome.setdefault("ssp", {})["summon_eligible"] = False
                path.write_text(json.dumps(genome, indent=2) + "\n", encoding="utf-8")
            elif step_name == "activation_order_removed" and not dry_run:
                genome = load_json(path)
                genome.setdefault("activation", {})["order"] = -1
                path.write_text(json.dumps(genome, indent=2) + "\n", encoding="utf-8")
            elif step_name == "shim_optional" and not dry_run:
                self._apply_shim_optional(gene, path)
            elif step_name == "code_removal_gated":
                state.notes["code_removal"] = (
                    "blocked until shim + two stable releases per retirement protocol"
                )

            state.completed_steps.append(step_name)
            state.current_step += 1

        state.notes["emission"] = self.emission_unused(gene)
        append_audit(
            "retirement_audit.jsonl",
            {
                "action": "retirement_advance",
                "gene": gene,
                "dry_run": dry_run,
                "step": state.current_step,
            },
        )
        self.save_state(state)
        return state

    def scan_all(
        self,
        *,
        dry_run: bool = True,
        target_step: int = 6,
    ) -> list[RetirementState]:
        results: list[RetirementState] = []
        for gene in sorted(GenomeEngine.registry().genomes):
            results.append(
                self.advance(gene, dry_run=dry_run, target_step=target_step)
            )
        return results


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Alt-4 Retirement Engine")
    parser.add_argument("--gene")
    parser.add_argument("--scan-all", action="store_true")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--step", type=int, default=6)
    args = parser.parse_args()

    engine = RetirementEngine()
    dry_run = not args.apply

    if args.scan_all:
        results = engine.scan_all(dry_run=dry_run, target_step=args.step)
        print(json.dumps([r.__dict__ for r in results], indent=2, default=str))
        return 0 if all(not r.failures for r in results) else 1

    if not args.gene:
        parser.error("--gene is required unless --scan-all is set")

    state = engine.advance(
        args.gene,
        dry_run=dry_run,
        target_step=args.step,
    )
    print(json.dumps(state.__dict__, indent=2, default=str))
    return 0 if not state.failures else 1


if __name__ == "__main__":
    import sys
    from pathlib import Path

    _root = Path(__file__).resolve().parents[2]
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    raise SystemExit(main())
