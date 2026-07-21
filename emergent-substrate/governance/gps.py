"""
GPS Constitution - Generative Profile Specification
Priority 20 - Blocks on profile axis drift, metaphor collapse, homogenization after 10 identical structure types
"""

from typing import List
from ..core.models import (
    StructuredModel,
    ValidationResult,
    GovernanceStatus,
    BaseConstitution
)


class GPSConstitution(BaseConstitution):
    """
    GPS: Generative Profile Specification
    Priority 20
    Blocks on:
    - Profile axis drift
    - Metaphor collapse
    - Homogenization after 10 identical structure types
    """
    
    name = "GPS"
    version = "1.0.0"
    priority = 20

    def __init__(self):
        super().__init__()
        self._structure_type_counts = {}
        self._profile_axes = {
            "creativity": 0.5,
            "coherence": 0.5,
            "novelty": 0.5,
            "depth": 0.5
        }

    def validate(self, model: StructuredModel) -> ValidationResult:
        """Validate model against GPS constraints"""
        violations = []
        warnings = []
        
        # Track structure type for homogenization check
        self._structure_type_counts[model.structure_type] = \
            self._structure_type_counts.get(model.structure_type, 0) + 1
        
        # Check for homogenization
        self._check_homogenization(model, violations, warnings)
        
        # Check for metaphor collapse
        self._check_metaphor_collapse(model, violations, warnings)
        
        # Check for profile axis drift
        self._check_profile_drift(model, violations, warnings)
        
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

    def _check_homogenization(self, model: StructuredModel, violations: List[str], warnings: List[str]):
        """Check for homogenization after 10 identical structure types"""
        count = self._structure_type_counts.get(model.structure_type, 0)
        
        if count >= 10:
            violations.append(f"GPS-R001: Homogenization detected - {count} identical '{model.structure_type}' structures")
        elif count >= 7:
            warnings.append(f"GPS-W001: Approaching homogenization - {count} identical '{model.structure_type}' structures")

    def _check_metaphor_collapse(self, model: StructuredModel, violations: List[str], warnings: List[str]):
        """Check for metaphor collapse"""
        if model.structure_type == "analogical":
            # Check if metaphor has sufficient depth
            if len(model.cross_domain_decomposition) < 2:
                violations.append("GPS-R002: Metaphor collapse - insufficient cross-domain depth")
            elif len(model.cross_domain_decomposition) < 3:
                warnings.append("GPS-W002: Metaphor weakening - limited cross-domain depth")
            
            # Check for metaphor degradation
            if model.confidence_score < 0.3:
                violations.append("GPS-R003: Metaphor collapse - low confidence score")

    def _check_profile_drift(self, model: StructuredModel, violations: List[str], warnings: List[str]):
        """Check for profile axis drift"""
        # Update profile axes based on model characteristics
        self._update_profile_axes(model)
        
        # Check for significant drift
        for axis, value in self._profile_axes.items():
            if value < 0.2:
                warnings.append(f"GPS-W003: Profile axis '{axis}' drifting low: {value:.2f}")
            elif value > 0.8:
                warnings.append(f"GPS-W004: Profile axis '{axis}' drifting high: {value:.2f}")

    def _update_profile_axes(self, model: StructuredModel):
        """Update profile axes based on model characteristics"""
        # Creativity: based on structure type diversity
        if model.structure_type not in self._structure_type_counts or self._structure_type_counts[model.structure_type] == 1:
            self._profile_axes["creativity"] = min(self._profile_axes["creativity"] + 0.05, 1.0)
        else:
            self._profile_axes["creativity"] = max(self._profile_axes["creativity"] - 0.02, 0.0)
        
        # Coherence: based on confidence score
        self._profile_axes["coherence"] = (
            self._profile_axes["coherence"] * 0.9 + model.confidence_score * 0.1
        )
        
        # Novelty: based on cross-domain diversity
        domain_diversity = len(model.cross_domain_decomposition)
        novelty_boost = min(domain_diversity * 0.1, 0.2)
        self._profile_axes["novelty"] = min(self._profile_axes["novelty"] + novelty_boost, 1.0)
        
        # Depth: based on invariant count
        depth_boost = min(len(model.invariants) * 0.05, 0.15)
        self._profile_axes["depth"] = min(self._profile_axes["depth"] + depth_boost, 1.0)

    def get_profile_axes(self) -> dict:
        """Get current profile axis values"""
        return self._profile_axes.copy()

    def reset_structure_counts(self):
        """Reset structure type counts"""
        self._structure_type_counts.clear()
