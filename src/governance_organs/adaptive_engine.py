"""Adaptive Engine — Governance Tier 5 contextual gates and health audits."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root, runtime_governance_dir
from src.governance_organs.genome_engine import GenomeEngine
from src.governance_organs.mutation_engine import MutationEngine
from src.governance_organs.promotion_engine import PromotionEngine
from src.governance_organs.retirement_engine import RetirementEngine

MATURITY_RANK = {"emergent": 0, "stable": 1, "constitutional": 2}


@dataclass
class ContextualGateResult:
    blocked: bool
    gate_id: str | None = None
    reason: str | None = None


class AdaptiveEngine:
    def __init__(self, root: Path | None = None):
        self.root = root or repo_root()

    @staticmethod
    def normalize_invariant(entry: Any) -> dict[str, str]:
        if isinstance(entry, str):
            return {"text": entry, "maturity": "stable"}
        if isinstance(entry, dict):
            return {
                "text": str(entry.get("text") or ""),
                "maturity": str(entry.get("maturity") or "stable"),
            }
        return {"text": "", "maturity": "emergent"}

    def health_check(self) -> dict[str, Any]:
        reg = GenomeEngine.reload(self.root)
        stages: dict[str, int] = {}
        tier5_genes: list[str] = []
        for gene, data in reg.genomes.items():
            stage = (data.get("identity") or {}).get("stage", "unknown")
            stages[stage] = stages.get(stage, 0) + 1
            gov = data.get("governance") or {}
            if gov.get("operator_lanes") or gov.get("contextual_gates"):
                tier5_genes.append(gene)

        promo = PromotionEngine(self.root)
        pending = [
            {
                "gene": r.gene,
                "from": r.current_stage,
                "to": r.target_stage,
                "failures": r.failures,
            }
            for r in promo.scan_all(apply=False, run_gates=False)
            if r.target_stage and not r.passed
        ]
        mutations = [
            {"mp_id": p.mp_id, "gene": p.gene, "status": p.status}
            for p in MutationEngine(self.root).list_proposals()
        ]
        retirement = RetirementEngine(self.root)
        retire_states = {
            gene: retirement.load_state(gene).current_step
            for gene in reg.genomes
        }
        report = {
            "genome_count": len(reg.genomes),
            "stage_histogram": stages,
            "tier5_enabled_genes": tier5_genes,
            "pending_promotions": pending,
            "mutation_proposals": mutations,
            "retirement_steps": retire_states,
        }
        out = runtime_governance_dir() / "tier5_health.json"
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        try:
            from src.adaptive_lane_organ import wake_adaptive_lanes

            lane_report = wake_adaptive_lanes(self.root)
            report["adaptive_lanes_awakened"] = lane_report.get("awakened", False)
            report["adaptive_lane_count"] = lane_report.get("lane_count", 0)
            try:
                from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

                fabric = build_coherence_fabric_status(root=self.root)
                report["coherence_fabric_aligned"] = bool(fabric.get("fabric_genes_aligned"))
                report["coherence_pipeline_allowed"] = bool(
                    fabric.get("coherence_pipeline_allowed")
                )
                report["safety_envelope_halt"] = bool(fabric.get("safety_envelope_halt"))
                report["mind_planes_aligned"] = bool(fabric.get("mind_planes_aligned"))
                report["infrastructure_substrate_aligned"] = bool(
                    fabric.get("infrastructure_substrate_aligned")
                )
                report["memory_paths_aligned"] = bool(fabric.get("memory_paths_aligned"))
                report["forensics_handoff_aligned"] = bool(
                    fabric.get("forensics_handoff_aligned")
                )
                report["immune_observe_aligned"] = bool(fabric.get("immune_observe_aligned"))
            except Exception:
                report["coherence_fabric_aligned"] = False
                report["coherence_pipeline_allowed"] = False
                report["safety_envelope_halt"] = False
                report["mind_planes_aligned"] = False
                report["infrastructure_substrate_aligned"] = False
                report["memory_paths_aligned"] = False
                report["forensics_handoff_aligned"] = False
                report["immune_observe_aligned"] = False
            out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        except Exception:
            report["adaptive_lanes_awakened"] = False
            report["adaptive_lane_count"] = 0
        return report

    def evaluate_context(
        self,
        runtime_context: str,
        capability_id: str | None,
        *,
        gene: str | None = None,
    ) -> ContextualGateResult:
        reg = GenomeEngine.registry()
        genes: list[str] = []
        if gene:
            genes = [gene]
        elif capability_id:
            resolved = GenomeEngine.resolve_gene(capability_id)
            if resolved:
                genes = [resolved]
        ctx = runtime_context.replace("-", "_").strip().lower()
        cap = (capability_id or "").replace("-", "_").strip().lower()

        for g in genes:
            data = reg.genomes.get(g)
            if not data:
                continue
            for gate in (data.get("governance") or {}).get("contextual_gates") or []:
                if not isinstance(gate, dict):
                    continue
                activate_on = [
                    str(a).replace("-", "_").lower() for a in (gate.get("activate_on") or [])
                ]
                if ctx not in activate_on and cap not in activate_on:
                    continue
                target = gate.get("make_target")
                if not target:
                    continue
                ok = self._run_gate_script(str(target))
                if not ok:
                    return ContextualGateResult(
                        blocked=True,
                        gate_id=str(gate.get("gate_id")),
                        reason=f"contextual gate {target} failed for {g}",
                    )
        return ContextualGateResult(blocked=False)

    def _run_gate_script(self, make_target: str) -> bool:
        from src.governance_organs.promotion_engine import GATE_SCRIPTS

        scripts = GATE_SCRIPTS.get(make_target)
        if not scripts:
            return True
        for script in scripts:
            path = self.root / script
            proc = subprocess.run(
                [sys.executable, str(path)],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
            if proc.returncode != 0:
                return False
        return True


class Tier5Governance:
    """Facade for Tier 5 adaptive governance."""

    adaptive = AdaptiveEngine

    @classmethod
    def wake_lanes(cls, root: Path | None = None) -> dict[str, Any]:
        from src.adaptive_lane_organ import wake_adaptive_lanes

        return wake_adaptive_lanes(root)

    @classmethod
    def health_check(cls, root: Path | None = None) -> dict[str, Any]:
        return AdaptiveEngine(root).health_check()

    @classmethod
    def tier5_gate(cls, root: Path | None = None) -> int:
        import subprocess

        script = (root or repo_root()) / "tools/governance/check_adaptive_governance.py"
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=root or repo_root(),
            check=False,
        )
        return int(proc.returncode)
