"""Promotion Engine — full-auto SSP lifecycle stage transitions."""

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

STAGE_ORDER = ("concept", "prototype", "mvp", "governed")

GENE_GATES: dict[str, str] = {
    "recipe_module": "recipe-module-gate",
    "imagine_generator": "imagine-generator-gate",
    "human_voice_extraction": "human-voice-extraction-gate",
    "narrative_trust_pack": "narrative-gate",
    "forensic_triangulation": "triangulation-gate",
    "cisiv_operator_lineage_console": "lineage-gate",
    "safety_envelope_organ": "safety-envelope-gate",
    "operator_profile_organ": "operator-profile-gate",
    "reflection_runtime_organ": "reflection-runtime-gate",
    "memory_runtime_organ": "memory-runtime-gate",
    "capability_service_bridge": "capability-bridge-gate",
    "jarvis_memory_board": "memory-board-gate",
    "governed_direct_pipeline": "governed-pipeline-gate",
    "adaptive_lane_organ": "adaptive-lane-gate",
    "operator_cognition_coherence_fabric": "coherence-fabric-gate",
    "continuity_witness_organ": "continuity-witness-gate",
    "narrative_continuity_organ": "narrative-continuity-gate",
    "intent_agency_organ": "intent-agency-gate",
    "phase_gate_organ": "phase-gate-organ-gate",
    "realtime_event_cause_predictor_organ": "realtime-predictor-organ-gate",
    "invariant_engine_organ": "invariant-engine-organ-gate",
    "verification_gate_organ": "verification-gate-organ-gate",
    "memory_path_governance_organ": "memory-path-governance-organ-gate",
    "knowledge_authority_organ": "knowledge-authority-organ-gate",
    "scorpion_bridge_organ": "scorpion-bridge-organ-gate",
    "mechanic_handoff_organ": "mechanic-handoff-organ-gate",
    "forensic_triangulation_organ": "forensic-triangulation-organ-gate",
    "immune_observe_organ": "immune-observe-organ-gate",
    "policy_gate_organ": "policy-gate-organ-gate",
    "predictor_immune_bridge_organ": "predictor-immune-bridge-organ-gate",
    "cognitive_bridge_organ": "cognitive-bridge-organ-gate",
    "governed_event_chain_organ": "governed-event-chain-organ-gate",
    "tracing_spine_organ": "tracing-spine-organ-gate",
    "mission_board_organ": "mission-board-organ-gate",
    "aris_boundary_organ": "aris-boundary-organ-gate",
    "capability_module_organ": "capability-module-organ-gate",
    "patchforge_organ": "patchforge-organ-gate",
    "change_scope_organ": "change-scope-organ-gate",
    "patch_verification_organ": "patch-verification-organ-gate",
    "otem_bounded_organ": "otem-bounded-organ-gate",
    "direct_challenge_organ": "direct-challenge-organ-gate",
    "orchestration_spine_organ": "orchestration-spine-organ-gate",
    "operator_health_sentinel_organ": "operator-health-sentinel-organ-gate",
    "governed_realtime_lane_organ": "governed-realtime-lane-organ-gate",
    "v8_runtime_organ": "v8-runtime-organ-gate",
    "patch_apply_organ": "patch-apply-organ-gate",
    "patch_execution_preview_organ": "patch-execution-preview-organ-gate",
    "run_ledger_organ": "run-ledger-organ-gate",
    "ul_lineage_console_organ": "ul-lineage-console-organ-gate",
    "module_governance_organ": "module-governance-organ-gate",
    "recipe_module_organ": "recipe-module-organ-gate",
    "imagine_generator_organ": "imagine-generator-organ-gate",
    "story_forge_lane_organ": "story-forge-lane-organ-gate",
    "beatbox_lane_organ": "beatbox-lane-organ-gate",
    "speakers_lane_organ": "speakers-lane-organ-gate",
    "human_voice_extraction_organ": "human-voice-extraction-organ-gate",
    "narrative_trust_pack_organ": "narrative-trust-pack-organ-gate",
}

GATE_SCRIPTS: dict[str, list[str]] = {
    "recipe-module-gate": [".github/scripts/check-recipe-module-governance.py"],
    "imagine-generator-gate": [".github/scripts/check-imagine-generator-governance.py"],
    "human-voice-extraction-gate": [
        ".github/scripts/check-human-voice-extraction-governance.py"
    ],
    "narrative-gate": [".github/scripts/check-narrative-governance.py"],
    "triangulation-gate": [".github/scripts/check-triangulation-governance.py"],
    "lineage-gate": [".github/scripts/check-lineage-governance.py"],
    "ssp-gate": ["tools/governance/check_ssp_completeness.py"],
    "genome-gate": ["tools/governance/check_subsystem_genome.py"],
    "safety-envelope-gate": [".github/scripts/check-safety-envelope-governance.py"],
    "operator-profile-gate": [".github/scripts/check-operator-profile-governance.py"],
    "reflection-runtime-gate": [".github/scripts/check-reflection-runtime-governance.py"],
    "memory-runtime-gate": [".github/scripts/check-memory-runtime-governance.py"],
    "adaptive-lane-gate": [".github/scripts/check-adaptive-lane-governance.py"],
    "coherence-fabric-gate": [".github/scripts/check-coherence-fabric-governance.py"],
    "capability-bridge-gate": [".github/scripts/check-capability-bridge-governance.py"],
    "memory-board-gate": [".github/scripts/check-memory-board-governance.py"],
    "governed-pipeline-gate": [".github/scripts/check-governed-pipeline-governance.py"],
    "continuity-witness-gate": [".github/scripts/check-continuity-witness-governance.py"],
    "narrative-continuity-gate": [".github/scripts/check-narrative-continuity-governance.py"],
    "intent-agency-gate": [".github/scripts/check-intent-agency-governance.py"],
    "phase-gate-organ-gate": [".github/scripts/check-phase-gate-organ-governance.py"],
    "realtime-predictor-organ-gate": [
        ".github/scripts/check-realtime-predictor-organ-governance.py"
    ],
    "invariant-engine-organ-gate": [
        ".github/scripts/check-invariant-engine-organ-governance.py"
    ],
    "verification-gate-organ-gate": [
        ".github/scripts/check-verification-gate-organ-governance.py"
    ],
    "memory-path-governance-organ-gate": [
        ".github/scripts/check-memory-path-governance-organ-governance.py"
    ],
    "knowledge-authority-organ-gate": [
        ".github/scripts/check-knowledge-authority-organ-governance.py"
    ],
    "scorpion-bridge-organ-gate": [
        ".github/scripts/check-scorpion-bridge-organ-governance.py"
    ],
    "mechanic-handoff-organ-gate": [
        ".github/scripts/check-mechanic-handoff-organ-governance.py"
    ],
    "forensic-triangulation-organ-gate": [
        ".github/scripts/check-forensic-triangulation-organ-governance.py"
    ],
    "immune-observe-organ-gate": [
        ".github/scripts/check-immune-observe-organ-governance.py"
    ],
    "policy-gate-organ-gate": [".github/scripts/check-policy-gate-organ-governance.py"],
    "predictor-immune-bridge-organ-gate": [
        ".github/scripts/check-predictor-immune-bridge-organ-governance.py"
    ],
    "cognitive-bridge-organ-gate": [
        ".github/scripts/check-cognitive-bridge-organ-governance.py"
    ],
    "governed-event-chain-organ-gate": [
        ".github/scripts/check-governed-event-chain-organ-governance.py"
    ],
    "tracing-spine-organ-gate": [".github/scripts/check-tracing-spine-organ-governance.py"],
    "mission-board-organ-gate": [".github/scripts/check-mission-board-organ-governance.py"],
    "aris-boundary-organ-gate": [".github/scripts/check-aris-boundary-organ-governance.py"],
    "capability-module-organ-gate": [
        ".github/scripts/check-capability-module-organ-governance.py"
    ],
    "patchforge-organ-gate": [".github/scripts/check-patchforge-organ-governance.py"],
    "change-scope-organ-gate": [".github/scripts/check-change-scope-organ-governance.py"],
    "patch-verification-organ-gate": [
        ".github/scripts/check-patch-verification-organ-governance.py"
    ],
    "otem-bounded-organ-gate": [".github/scripts/check-otem-bounded-organ-governance.py"],
    "direct-challenge-organ-gate": [
        ".github/scripts/check-direct-challenge-organ-governance.py"
    ],
    "orchestration-spine-organ-gate": [
        ".github/scripts/check-orchestration-spine-organ-governance.py"
    ],
    "operator-health-sentinel-organ-gate": [
        ".github/scripts/check-operator-health-sentinel-organ-governance.py"
    ],
    "governed-realtime-lane-organ-gate": [
        ".github/scripts/check-governed-realtime-lane-organ-governance.py"
    ],
    "v8-runtime-organ-gate": [".github/scripts/check-v8-runtime-organ-governance.py"],
    "patch-apply-organ-gate": [".github/scripts/check-patch-apply-organ-governance.py"],
    "patch-execution-preview-organ-gate": [
        ".github/scripts/check-patch-execution-preview-organ-governance.py"
    ],
    "run-ledger-organ-gate": [".github/scripts/check-run-ledger-organ-governance.py"],
    "ul-lineage-console-organ-gate": [
        ".github/scripts/check-ul-lineage-console-organ-governance.py"
    ],
    "module-governance-organ-gate": [
        ".github/scripts/check-module-governance-organ-governance.py"
    ],
    "recipe-module-organ-gate": [".github/scripts/check-recipe-module-organ-governance.py"],
    "imagine-generator-organ-gate": [
        ".github/scripts/check-imagine-generator-organ-governance.py"
    ],
    "story-forge-lane-organ-gate": [
        ".github/scripts/check-story-forge-lane-organ-governance.py"
    ],
    "beatbox-lane-organ-gate": [".github/scripts/check-beatbox-lane-organ-governance.py"],
    "speakers-lane-organ-gate": [".github/scripts/check-speakers-lane-organ-governance.py"],
    "human-voice-extraction-organ-gate": [
        ".github/scripts/check-human-voice-extraction-organ-governance.py"
    ],
    "narrative-trust-pack-organ-gate": [
        ".github/scripts/check-narrative-trust-pack-organ-governance.py"
    ],
}

PROTOTYPE_GATE_STUB_GENES = frozenset(GENE_GATES.keys()) | frozenset(
    {
        "capability_service_bridge",
        "jarvis_memory_board",
        "governed_direct_pipeline",
    }
)

MUTATION_CONTRACT = "docs/contracts/AAIS_SUBSYSTEM_MUTATION_PATH.md"
RETIREMENT_CONTRACT = "docs/contracts/AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md"


@dataclass
class PromotionDecision:
    gene: str
    passed: bool
    current_stage: str
    target_stage: str | None
    failures: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)


class PromotionEngine:
    def __init__(self, root: Path | None = None):
        self.root = root or repo_root()

    def _genome_path(self, gene: str) -> Path:
        path = GenomeEngine.registry().paths.get(gene)
        if path is None:
            raise KeyError(f"unknown gene: {gene}")
        return path

    def _read_genome(self, gene: str) -> dict[str, Any]:
        return load_json(self._genome_path(gene))

    def _write_genome(self, gene: str, data: dict[str, Any]) -> None:
        path = self._genome_path(gene)
        backup_dir = runtime_governance_dir() / "promotion_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        shutil.copy2(path, backup_dir / f"{gene}_{stamp}.genome.v1.json")
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        GenomeEngine.reload(self.root)

    def _run_gate(self, target: str) -> tuple[bool, str]:
        import sys

        scripts = GATE_SCRIPTS.get(target)
        if scripts:
            outputs: list[str] = []
            for script in scripts:
                path = self.root / script
                try:
                    proc = subprocess.run(
                        [sys.executable, str(path)],
                        cwd=self.root,
                        capture_output=True,
                        text=True,
                        timeout=600,
                        check=False,
                    )
                except (OSError, subprocess.TimeoutExpired) as exc:
                    return False, str(exc)
                outputs.append((proc.stdout or "") + (proc.stderr or ""))
                if proc.returncode != 0:
                    return False, "\n".join(outputs).strip()
            return True, "\n".join(outputs).strip()

        try:
            proc = subprocess.run(
                ["make", target],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
        except FileNotFoundError:
            return False, "make not found and no gate script mapping"
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, str(exc)
        output = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, output.strip()

    def _has_cross_reference(self, gene: str, data: dict[str, Any]) -> bool:
        lineage = data.get("lineage") or {}
        if lineage.get("children"):
            return True
        for other_gene, other in GenomeEngine.registry().genomes.items():
            if gene in (other.get("lineage") or {}).get("children", []):
                return True
        return False

    def _has_invariant_tests(self, gene: str) -> bool:
        tests_dir = self.root / "tests"
        patterns = [
            f"test_{gene}.py",
            f"test_{gene.replace('_', '')}.py",
        ]
        for pattern in patterns:
            if (tests_dir / pattern).is_file():
                return True
        partial = gene.split("_")[0]
        for path in tests_dir.glob(f"test_*{partial}*.py"):
            if gene.replace("_", "") in path.name.replace("_", "") or gene in path.name:
                return True
        return False

    def _contracts_cover_lifecycle(self, data: dict[str, Any]) -> bool:
        contracts = [str(c) for c in (data.get("governance") or {}).get("contracts") or []]
        has_mutation = any("MUTATION" in c.upper() for c in contracts)
        has_retirement = any("RETIREMENT" in c.upper() for c in contracts)
        return has_mutation and has_retirement

    def _next_stage(self, current: str) -> str | None:
        if current not in STAGE_ORDER:
            return None
        idx = STAGE_ORDER.index(current)
        if idx + 1 >= len(STAGE_ORDER):
            return None
        return STAGE_ORDER[idx + 1]

    def evaluate(self, gene: str, *, run_gates: bool = True) -> PromotionDecision:
        reg = GenomeEngine.reload(self.root)
        if gene not in reg.genomes:
            return PromotionDecision(
                gene=gene,
                passed=False,
                current_stage="",
                target_stage=None,
                failures=[f"gene not in registry: {gene}"],
            )

        data = reg.genomes[gene]
        current = (data.get("identity") or {}).get("stage", "")
        target = self._next_stage(current)
        failures: list[str] = []
        artifacts: list[str] = []

        if target is None:
            return PromotionDecision(
                gene=gene,
                passed=True,
                current_stage=current,
                target_stage=None,
                failures=[],
                artifacts=["already at terminal promotable stage"],
            )

        if target == "prototype":
            if run_gates:
                ssp_ok, ssp_out = self._run_gate("ssp-gate")
                artifacts.append("make ssp-gate")
                if not ssp_ok:
                    failures.append(f"ssp-gate failed: {ssp_out[-400:]}")
            proof = data.get("proof") or {}
            for bundle in proof.get("bundles") or []:
                if "PROTOTYPE" in bundle.upper():
                    artifacts.append(bundle)
            surface = (data.get("runtime") or {}).get("surface") or []
            if not surface:
                failures.append("prototype requires runtime.surface entries")
            for entry in surface:
                if isinstance(entry, dict) and entry.get("isolated") is not True:
                    failures.append("prototype surface entries must be isolated")

        if target == "mvp":
            gate = GENE_GATES.get(gene)
            if gate:
                artifacts.append(f"make {gate}")
                if run_gates:
                    ok, out = self._run_gate(gate)
                    if not ok:
                        failures.append(f"{gate} failed: {out[-400:]}")
            else:
                failures.append(f"no gene gate defined for {gene}")
            proof = data.get("proof") or {}
            bundles = proof.get("bundles") or []
            if not bundles:
                failures.append("mvp requires proof.bundles")
            for bundle in bundles:
                if not (self.root / bundle).is_file():
                    failures.append(f"missing proof bundle: {bundle}")
            surface = (data.get("runtime") or {}).get("surface") or []
            if not surface:
                failures.append("mvp requires runtime.surface")

        if target == "governed":
            gate = GENE_GATES.get(gene)
            if gate:
                artifacts.append(f"make {gate}")
                if run_gates:
                    ok, out = self._run_gate(gate)
                    if not ok:
                        failures.append(f"{gate} failed: {out[-400:]}")
            artifacts.append("make genome-gate")
            if run_gates:
                ok, out = self._run_gate("genome-gate")
                if not ok:
                    failures.append(f"genome-gate failed: {out[-400:]}")
            if not self._has_invariant_tests(gene):
                failures.append("governed requires invariant tests under tests/")
            if not self._has_cross_reference(gene, data):
                failures.append(
                    "governed requires lineage.children or reference from another genome"
                )
            if not self._contracts_cover_lifecycle(data):
                if (self.root / MUTATION_CONTRACT).is_file() and (
                    self.root / RETIREMENT_CONTRACT
                ).is_file():
                    artifacts.append("lifecycle contracts injectable on governed apply")
                else:
                    failures.append(
                        "governed requires mutation and retirement contract docs on disk"
                    )
            proof = data.get("proof") or {}
            for bundle in proof.get("bundles") or []:
                if not (self.root / bundle).is_file():
                    failures.append(f"missing proof bundle: {bundle}")

        return PromotionDecision(
            gene=gene,
            passed=not failures,
            current_stage=current,
            target_stage=target,
            failures=failures,
            artifacts=artifacts,
        )

    def _append_logbook(self, gene: str, target: str, display_name: str) -> None:
        logbook = self.root / "docs/audit/LOGBOOK.md"
        title_map = {
            "prototype": "Prototype Promotion",
            "mvp": "MVP Promotion",
            "governed": "Governed Promotion",
        }
        title = title_map.get(target, f"{target.title()} Promotion")
        entry = (
            f"\n### {display_name} — {title} (Alt-4 Runtime)\n\n"
            f"- CISIV stage: `verification`\n"
            f"- scope: Promotion Engine full-auto — `{gene}` "
            f"`{target}` via Alt-4 runtime organ\n"
            f"- outcome: genome `identity.stage` and `proof.posture` set to `{target}`\n"
            f"- verification note: `make genome-gate`; `make alt4-gate`\n"
        )
        text = logbook.read_text(encoding="utf-8")
        if f"### {display_name} — {title} (Alt-4 Runtime)" in text:
            return
        logbook.write_text(text.rstrip() + entry, encoding="utf-8")

    def _update_subsystem_spec_governed(self, gene: str, display_name: str) -> None:
        spec_path = self.root / "docs/runtime/AAIS_SUBSYSTEM_SPEC.md"
        text = spec_path.read_text(encoding="utf-8")
        if f"| {display_name} | governed |" in text:
            return
        pattern = re.compile(
            rf"\| {re.escape(display_name)} \| partial \|",
        )
        replacement = f"| {display_name} | governed |"
        if pattern.search(text):
            spec_path.write_text(pattern.sub(replacement, text), encoding="utf-8")

    def apply(self, decision: PromotionDecision, *, dry_run: bool = False) -> PromotionDecision:
        append_audit(
            "promotion_audit.jsonl",
            {
                "action": "promotion_apply",
                "dry_run": dry_run,
                "gene": decision.gene,
                "target_stage": decision.target_stage,
                "passed": decision.passed,
                "failures": decision.failures,
            },
        )
        if not decision.passed or not decision.target_stage:
            return decision
        if decision.current_stage == decision.target_stage:
            return decision

        data = self._read_genome(decision.gene)
        identity = data.setdefault("identity", {})
        proof = data.setdefault("proof", {})
        schema = data.setdefault("schema", {})
        gov = data.setdefault("governance", {})
        retirement = data.setdefault("retirement", {})

        target = decision.target_stage
        identity["stage"] = target
        proof["posture"] = target

        if target == "governed":
            schema["frozen"] = True
            contracts = list(gov.get("contracts") or [])
            for path in (MUTATION_CONTRACT, RETIREMENT_CONTRACT):
                if path not in contracts:
                    contracts.append(path)
            gov["contracts"] = contracts
            if not retirement.get("path"):
                retirement["path"] = RETIREMENT_CONTRACT
            version = str(identity.get("version") or "1.0.0-mvp")
            if "mvp" in version:
                identity["version"] = version.replace("-mvp", "-governed")
            display = identity.get("display_name") or decision.gene

        if dry_run:
            return decision

        try:
            self._write_genome(decision.gene, data)
            display = (data.get("identity") or {}).get("display_name") or decision.gene
            self._append_logbook(decision.gene, target, display)
            if target == "governed":
                self._update_subsystem_spec_governed(decision.gene, display)
            ok, out = self._run_gate("genome-gate")
            if not ok:
                self.rollback(decision.gene)
                decision.passed = False
                decision.failures.append(f"post-apply genome-gate failed: {out[-400:]}")
        except Exception as exc:
            decision.passed = False
            decision.failures.append(f"apply failed: {exc}")
        return decision

    def rollback(self, gene: str) -> bool:
        backup_dir = runtime_governance_dir() / "promotion_backups"
        backups = sorted(backup_dir.glob(f"{gene}_*.genome.v1.json"))
        if not backups:
            return False
        latest = backups[-1]
        shutil.copy2(latest, self._genome_path(gene))
        GenomeEngine.reload(self.root)
        append_audit(
            "promotion_audit.jsonl",
            {"action": "promotion_rollback", "gene": gene, "restored": str(latest)},
        )
        return True

    def scan_all(
        self,
        *,
        apply: bool = False,
        dry_run: bool = False,
        run_gates: bool = True,
    ) -> list[PromotionDecision]:
        results: list[PromotionDecision] = []
        for gene in sorted(GenomeEngine.registry().genomes):
            decision = self.evaluate(gene, run_gates=run_gates)
            if apply and decision.passed and decision.target_stage:
                decision = self.apply(decision, dry_run=dry_run)
            results.append(decision)
        return results


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Alt-4 Promotion Engine")
    parser.add_argument("--gene", help="Subsystem gene to evaluate")
    parser.add_argument("--apply", action="store_true", help="Apply promotion if eligible")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate apply without writes")
    parser.add_argument("--scan-all", action="store_true", help="Scan entire registry")
    args = parser.parse_args()

    engine = PromotionEngine()
    GenomeEngine.validate_registry()

    if args.scan_all:
        results = engine.scan_all(apply=args.apply, dry_run=args.dry_run)
        failed = [r for r in results if not r.passed and r.target_stage]
        for result in results:
            status = "PASS" if result.passed else "FAIL"
            print(
                f"[promotion] {status} {result.gene}: "
                f"{result.current_stage} -> {result.target_stage or '—'}"
            )
            for failure in result.failures:
                print(f"  - {failure}")
        return 1 if failed else 0

    if not args.gene:
        parser.error("--gene or --scan-all required")
        return 2

    decision = engine.evaluate(args.gene)
    if args.apply:
        decision = engine.apply(decision, dry_run=args.dry_run)
    print(json.dumps(decision.__dict__, indent=2))
    return 0 if decision.passed else 1


if __name__ == "__main__":
    import sys
    from pathlib import Path

    _root = Path(__file__).resolve().parents[2]
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    raise SystemExit(main())
