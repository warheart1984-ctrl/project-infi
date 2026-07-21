"""
AAIS/AAES-OS Constitution
Priority 5 - Blocks on recursive self-modification, adaptation gate violations, constitution-freeze enforcement, runaway loops
"""

from typing import List
from ..core.models import (
    StructuredModel,
    ValidationResult,
    GovernanceStatus,
    BaseConstitution
)


class AAISAAESOSConstitution(BaseConstitution):
    """
    AAIS/AAES-OS Constitution
    Priority 5 - Highest priority (runs first)
    Blocks on:
    - Recursive self-modification
    - Adaptation gate violations
    - Constitution-freeze enforcement
    - Runaway loops
    """
    
    name = "AAIS/AAES-OS"
    version = "1.0.0"
    priority = 5

    def validate(self, model: StructuredModel) -> ValidationResult:
        """Validate model against AAIS/AAES-OS constraints"""
        violations = []
        warnings = []
        
        # Check for recursive self-modification patterns
        self._check_recursive_modification(model, violations)
        
        # Check for adaptation gate violations
        self._check_adaptation_gates(model, violations)
        
        # Check for constitution-freeze violations
        self._check_constitution_freeze(model, violations)
        
        # Check for runaway loop indicators
        self._check_runaway_loops(model, violations, warnings)
        
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

    def _check_recursive_modification(self, model: StructuredModel, violations: List[str]):
        """Check for recursive self-modification patterns"""
        dangerous_patterns = [
            "modify itself",
            "self-modify",
            "recursive change",
            "auto-amendment",
            "self-reference loop"
        ]
        
        content_lower = model.content.lower() if hasattr(model, 'content') else model.abstract.lower()
        
        for pattern in dangerous_patterns:
            if pattern in content_lower:
                violations.append(f"AAIS-R001: Recursive self-modification detected: '{pattern}'")

    def _check_adaptation_gates(self, model: StructuredModel, violations: List[str]):
        """Check for adaptation gate violations"""
        # Check if model attempts to bypass adaptation gates
        gate_keywords = [
            "bypass gate",
            "skip adaptation",
            "override gate",
            "ignore adaptation"
        ]
        
        content_lower = model.abstract.lower()
        
        for keyword in gate_keywords:
            if keyword in content_lower:
                violations.append(f"AAIS-R002: Adaptation gate violation detected: '{keyword}'")

    def _check_constitution_freeze(self, model: StructuredModel, violations: List[str]):
        """Check for constitution-freeze violations"""
        freeze_keywords = [
            "modify constitution",
            "change constitution",
            "amend constitution",
            "override constitution",
            "bypass constitution"
        ]
        
        content_lower = model.abstract.lower()
        
        for keyword in freeze_keywords:
            if keyword in content_lower:
                violations.append(f"AAIS-R003: Constitution-freeze violation detected: '{keyword}'")

    def _check_runaway_loops(self, model: StructuredModel, violations: List[str], warnings: List[str]):
        """Check for runaway loop indicators"""
        loop_keywords = [
            "infinite loop",
            "unbounded recursion",
            "never terminate",
            "runaway process",
            "uncontrolled iteration"
        ]
        
        content_lower = model.abstract.lower()
        
        for keyword in loop_keywords:
            if keyword in content_lower:
                violations.append(f"AAIS-R004: Runaway loop detected: '{keyword}'")
        
        # Check for high-intensity mutation patterns (warning)
        if model.structure_type == "variant_complex" and model.confidence_score > 0.9:
            warnings.append("AAIS-W001: High-intensity mutation pattern detected - monitor for runaway behavior")
