"""Mutation Engine (MP-X) — backward-compatible schema evolution with rollback."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
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

FABRIC_MINIMUM_GENES = frozenset(
    {
        "adaptive_lane_organ",
        "operator_profile_organ",
        "capability_service_bridge",
        "recipe_module",
        "governed_direct_pipeline",
    }
)

SUPPORTED_LANE_OPS = frozenset({"append_capabilities", "add_lane"})
FORBIDDEN_LANE_OPS = frozenset({"rename_lane", "decrease_weight", "override_authority"})


@dataclass
class MutationProposal:
    mp_id: str
    gene: str
    status: str
    backward_compatible: bool
    schema_delta_ref: str | None
    path: Path
    raw: dict[str, str] = field(default_factory=dict)

    @property
    def mutation_kind(self) -> str | None:
        return self.raw.get("mutation_kind")

    @property
    def operator_lanes_delta_ref(self) -> str | None:
        return self.raw.get("operator_lanes_delta_ref") or self.schema_delta_ref

    @property
    def post_apply_wake(self) -> bool:
        return self.raw.get("post_apply_wake", "").lower() in {"true", "yes", "1"}

    @property
    def post_apply_gate(self) -> str | None:
        return self.raw.get("post_apply_gate")

    @property
    def fabric_genes(self) -> list[str]:
        raw = self.raw.get("fabric_genes", "")
        if not raw:
            return [self.gene]
        cleaned = raw.strip("[]")
        return [part.strip() for part in cleaned.split(",") if part.strip()]


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

    def _lane_delta_path(self, proposal: MutationProposal) -> Path | None:
        ref = proposal.operator_lanes_delta_ref
        if not ref:
            return None
        return self.root / ref

    def _validate_lane_delta(self, delta: Any) -> list[str]:
        failures: list[str] = []
        if not isinstance(delta, dict):
            return ["lane delta must be a JSON object"]
        if delta.get("mutation_kind") != "lane_dna":
            failures.append("lane delta mutation_kind must be lane_dna")
        patches = delta.get("patches")
        if not isinstance(patches, list) or not patches:
            failures.append("lane delta patches must be a non-empty array")
            return failures
        for index, patch in enumerate(patches):
            if not isinstance(patch, dict):
                failures.append(f"lane delta patches[{index}] must be object")
                continue
            op = patch.get("op")
            if op in FORBIDDEN_LANE_OPS:
                failures.append(f"lane delta patches[{index}] op forbidden: {op}")
            elif op not in SUPPORTED_LANE_OPS:
                failures.append(f"lane delta patches[{index}] unsupported op: {op}")
            elif op == "append_capabilities":
                if not str(patch.get("lane_id") or "").strip():
                    failures.append(f"lane delta patches[{index}] missing lane_id")
                caps = patch.get("capabilities")
                if not isinstance(caps, list) or not caps:
                    failures.append(f"lane delta patches[{index}] capabilities required")
            elif op == "add_lane":
                lane = patch.get("lane")
                if not isinstance(lane, dict) or not str(lane.get("lane_id") or "").strip():
                    failures.append(f"lane delta patches[{index}] add_lane requires lane.lane_id")
                if not isinstance(lane, dict) or not lane.get("capabilities"):
                    failures.append(f"lane delta patches[{index}] add_lane requires capabilities")
        return failures

    def _apply_lane_delta(self, data: dict[str, Any], delta: dict[str, Any]) -> list[str]:
        failures = self._validate_lane_delta(delta)
        if failures:
            return failures
        gov = data.setdefault("governance", {})
        lanes = [dict(lane) for lane in (gov.get("operator_lanes") or []) if isinstance(lane, dict)]
        for patch in delta.get("patches") or []:
            op = patch.get("op")
            if op == "append_capabilities":
                lane_id = str(patch.get("lane_id") or "").strip()
                caps = [str(cap) for cap in (patch.get("capabilities") or [])]
                found = False
                for lane in lanes:
                    if str(lane.get("lane_id") or "") == lane_id:
                        existing = [str(cap) for cap in (lane.get("capabilities") or [])]
                        for cap in caps:
                            if cap not in existing:
                                existing.append(cap)
                        lane["capabilities"] = existing
                        found = True
                        break
                if not found:
                    failures.append(f"lane_id {lane_id!r} not found for append_capabilities")
            elif op == "add_lane":
                lane_obj = dict(patch.get("lane") or {})
                lane_id = str(lane_obj.get("lane_id") or "").strip()
                if any(str(lane.get("lane_id") or "") == lane_id for lane in lanes):
                    failures.append(f"lane_id {lane_id!r} already exists")
                    continue
                lanes.append(lane_obj)
        gov["operator_lanes"] = lanes
        return failures

    def _append_invariant(self, gov: dict[str, Any], invariant: str | None) -> None:
        if not invariant:
            return
        invariants = list(gov.get("invariants") or [])
        for entry in invariants:
            if isinstance(entry, str) and entry == invariant:
                return
            if isinstance(entry, dict) and entry.get("text") == invariant:
                return
        needs_maturity = any(isinstance(entry, dict) and entry.get("maturity") for entry in invariants)
        if needs_maturity:
            invariants.append({"text": invariant, "maturity": "stable"})
        else:
            invariants.append(invariant)
        gov["invariants"] = invariants

    def _run_subprocess(self, script: Path, *, label: str) -> list[str]:
        if not script.is_file():
            return [f"{label} script missing: {script.relative_to(self.root)}"]
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        if proc.returncode != 0:
            detail = (proc.stdout or proc.stderr or "").strip().splitlines()
            suffix = detail[-1] if detail else "non-zero exit"
            return [f"{label} failed: {suffix}"]
        return []

    def _post_apply_hooks(self, proposal: MutationProposal) -> list[str]:
        failures: list[str] = []
        if proposal.post_apply_wake:
            from src.adaptive_lane_organ import wake_adaptive_lanes

            report = wake_adaptive_lanes(self.root)
            if not report.get("awakened"):
                failures.append("post-apply wake did not awaken adaptive lanes")
        fabric_overlap = FABRIC_MINIMUM_GENES.intersection(proposal.fabric_genes)
        run_alt6 = proposal.post_apply_gate == "alt6-governed-gate" or (
            proposal.mutation_kind == "lane_dna" and bool(fabric_overlap)
        )
        run_alt7 = proposal.post_apply_gate == "alt7-governed-gate" or (
            proposal.mutation_kind == "lane_dna" and bool(fabric_overlap)
        )
        if run_alt6 and fabric_overlap:
            script = self.root / "tools/governance/check_alt6_governed_eligibility.py"
            failures.extend(self._run_subprocess(script, label="alt6-governed-gate"))
        if run_alt7:
            script = self.root / "tools/governance/check_alt7_governed_eligibility.py"
            failures.extend(self._run_subprocess(script, label="alt7-governed-gate"))
        if proposal.post_apply_gate == "narrative-gate":
            script = self.root / ".github/scripts/check-narrative-governance.py"
            failures.extend(self._run_subprocess(script, label="narrative-gate"))
        elif proposal.post_apply_gate == "operator-profile-gate":
            script = self.root / ".github/scripts/check-operator-profile-governance.py"
            failures.extend(self._run_subprocess(script, label="operator-profile-gate"))
        if proposal.mutation_kind == "profile_invariant":
            script = self.root / "tools/governance/check_alt7_governed_eligibility.py"
            failures.extend(self._run_subprocess(script, label="alt7-governed-gate"))
        if proposal.raw.get("post_apply_snapshot_check", "").lower() in {"true", "yes", "1"}:
            from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

            status = build_coherence_fabric_status(root=self.root)
            if not status.get("fabric_genes_aligned"):
                failures.append("post-apply coherence snapshot not aligned")
        return failures

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
        if proposal.mutation_kind == "lane_dna":
            delta_path = self._lane_delta_path(proposal)
            if delta_path is None or not delta_path.is_file():
                failures.append(
                    f"operator_lanes delta missing: {proposal.operator_lanes_delta_ref}"
                )
            else:
                failures.extend(self._validate_lane_delta(load_json(delta_path)))
        elif proposal.schema_delta_ref:
            delta_path = self.root / proposal.schema_delta_ref
            if not delta_path.is_file():
                failures.append(f"schema delta missing: {proposal.schema_delta_ref}")

        script = self.root / "tools/governance/check_subsystem_genome.py"
        failures.extend(self._run_subprocess(script, label="genome-gate"))

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

        if proposal.mutation_kind == "lane_dna":
            delta_path = self._lane_delta_path(proposal)
            assert delta_path is not None
            lane_failures = self._apply_lane_delta(data, load_json(delta_path))
            if lane_failures:
                return MutationResult(
                    mp_id=mp_id,
                    gene=gene,
                    passed=False,
                    failures=lane_failures,
                )

        self._append_invariant(gov, invariant)

        history = data.setdefault("mutation", {}).setdefault("history", [])
        history.append(
            {
                "proposal_id": mp_id,
                "status": "promoted",
                "schema_delta_ref": proposal.operator_lanes_delta_ref or proposal.schema_delta_ref,
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

        hook_failures = self._post_apply_hooks(proposal)
        if hook_failures:
            self.rollback(gene, mp_id)
            return MutationResult(
                mp_id=mp_id,
                gene=gene,
                passed=False,
                failures=hook_failures,
            )

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
        proposal = next((p for p in self.list_proposals(gene) if p.mp_id == mp_id), None)
        if proposal and proposal.post_apply_wake:
            from src.adaptive_lane_organ import wake_adaptive_lanes

            wake_adaptive_lanes(self.root)
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
    _root = Path(__file__).resolve().parents[2]
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    raise SystemExit(main())
