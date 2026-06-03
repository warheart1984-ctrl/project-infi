"""Alt-4 Runtime — governance organs (Promotion, Retirement, Mutation, Genome)."""

from __future__ import annotations

from src.governance_organs.genome_engine import GenomeEngine, GenomeValidationError
from src.governance_organs.mutation_engine import MutationEngine
from src.governance_organs.promotion_engine import PromotionEngine
from src.governance_organs.retirement_engine import RetirementEngine
from src.governance_organs.adaptive_engine import AdaptiveEngine, Tier5Governance
from src.governance_organs.linguistic_governance_engine import LinguisticGovernanceEngine
from src.governance_organs.linguistic_governance_cycle_engine import (
    LinguisticGovernanceCycleEngine,
)
from src.governance_organs.linguistic_predictive_governance_engine import (
    LinguisticPredictiveGovernanceEngine,
)


class LinguisticGovernanceRuntime:
    """Facade for meta-linguistic gates, cycle, predictive cycle, drift/cascade."""

    linguistic = LinguisticGovernanceEngine
    cycle = LinguisticGovernanceCycleEngine
    predictive = LinguisticPredictiveGovernanceEngine


class Alt4Runtime:
    """Facade for boot, gates, and lifecycle orchestration."""

    genome = GenomeEngine
    promotion = PromotionEngine
    retirement = RetirementEngine
    mutation = MutationEngine

    @classmethod
    def boot_validate(cls) -> None:
        cls.genome.validate_registry_boot()

    @classmethod
    def reload(cls) -> None:
        cls.genome.reload()

    @classmethod
    def alt4_gate(cls, *, strict: bool | None = None) -> int:
        import os

        if strict is None:
            env = os.getenv("AAIS_ALT4_GATE_STRICT", "").strip().lower()
            strict = env in {"1", "true", "yes"}
        cls.genome.validate_registry()
        engine = PromotionEngine()
        results = engine.scan_all(apply=False)
        pending = [r for r in results if r.target_stage and not r.passed]
        for result in pending:
            print(
                f"[alt4-gate] promotion pending {result.gene} "
                f"({result.current_stage} -> {result.target_stage})"
            )
            for failure in result.failures:
                print(f"[alt4-gate]   - {failure}")
        print(
            f"[alt4-gate] PASS: {len(cls.genome.registry().genomes)} genome(s) valid; "
            f"{len(pending)} pending promotion(s)"
        )
        if strict and pending:
            print("[alt4-gate] FAIL: strict mode — pending promotions block gate")
            return 1
        import os

        if os.getenv("AAIS_META_LINGUISTIC_GATE", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }:
            ling = LinguisticGovernanceEngine()
            ling_report = ling.run_all_gates(strict=strict)
            if not ling_report.passed:
                print("[alt4-gate] FAIL: meta-linguistic-gate failed")
                return 1
        return 0


__all__ = [
    "LinguisticGovernanceRuntime",
    "LinguisticGovernanceEngine",
    "LinguisticGovernanceCycleEngine",
    "LinguisticPredictiveGovernanceEngine",
    "Alt4Runtime",
    "AdaptiveEngine",
    "Tier5Governance",
    "GenomeEngine",
    "GenomeValidationError",
    "PromotionEngine",
    "RetirementEngine",
    "MutationEngine",
]
