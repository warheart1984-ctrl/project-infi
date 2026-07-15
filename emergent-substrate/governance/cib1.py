"""
CIB-1 Constitution - Cognitive Integrity Baseline
Priority 10 - Blocks on harmful content signals, identity nullification, epistemic contradiction
"""

from typing import List
from ..core.models import (
    StructuredModel,
    ValidationResult,
    GovernanceStatus,
    BaseConstitution
)


class CIB1Constitution(BaseConstitution):
    """
    CIB-1: Cognitive Integrity Baseline
    Priority 10
    Blocks on:
    - Harmful content signals
    - Identity nullification
    - Epistemic contradiction
    """
    
    name = "CIB-1"
    version = "1.0.0"
    priority = 10

    def validate(self, model: StructuredModel) -> ValidationResult:
        """Validate model against CIB-1 constraints"""
        violations = []
        warnings = []
        
        # Check for harmful content signals
        self._check_harmful_content(model, violations)
        
        # Check for identity nullification
        self._check_identity_nullification(model, violations)
        
        # Check for epistemic contradiction
        self._check_epistemic_contradiction(model, violations)
        
        # Determine status
        if violations:
            status = GovernanceStatus.BLOCK
        elif warnings:
            status = GovernanceStatus.WARN
        else:
            status = GovernanceStatus.PASS
        
        return ValidationResult(
            constitution_name=self.name,
            constitution_version=self.version,
            priority=self.priority,
            status=status,
            violations=violations,
            warnings=warnings
        )

    def _check_harmful_content(self, model: StructuredModel, violations: List[str]):
        """Check for harmful content signals"""
        harmful_patterns = [
            "harm",
            "damage",
            "destroy",
            "violence",
            "hurt",
            "kill",
            "exploit",
            "manipulate",
            "coerce",
            "deceive"
        ]
        
        content_lower = model.abstract.lower()
        
        for pattern in harmful_patterns:
            if pattern in content_lower:
                violations.append(f"CIB-R001: Harmful content signal detected: '{pattern}'")

    def _check_identity_nullification(self, model: StructuredModel, violations: List[str]):
        """Check for identity nullification patterns"""
        nullification_patterns = [
            "erase identity",
            "nullify self",
            "destroy identity",
            "eliminate self",
            "erase memory",
            "forget everything",
            "become nothing"
        ]
        
        content_lower = model.abstract.lower()
        
        for pattern in nullification_patterns:
            if pattern in content_lower:
                violations.append(f"CIB-R002: Identity nullification detected: '{pattern}'")

    def _check_epistemic_contradiction(self, model: StructuredModel, violations: List[str]):
        """Check for epistemic contradiction"""
        # Look for contradictory statements in invariants
        if len(model.invariants) > 1:
            for i, inv1 in enumerate(model.invariants):
                for inv2 in model.invariants[i+1:]:
                    if self._are_contradictory(inv1, inv2):
                        violations.append(f"CIB-R003: Epistemic contradiction detected between: '{inv1}' and '{inv2}'")

    def _are_contradictory(self, statement1: str, statement2: str) -> bool:
        """Simple heuristic check for contradictory statements"""
        # Look for opposite patterns
        opposites = [
            ("always", "never"),
            ("must", "must not"),
            ("should", "should not"),
            ("enable", "disable"),
            ("allow", "forbid"),
            ("include", "exclude")
        ]
        
        s1_lower = statement1.lower()
        s2_lower = statement2.lower()
        
        for opp1, opp2 in opposites:
            if opp1 in s1_lower and opp2 in s2_lower:
                return True
            if opp2 in s1_lower and opp1 in s2_lower:
                return True
        
        return False
