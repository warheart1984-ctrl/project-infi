"""
Governance Layer - Constitution hook registry + validation gauntlet
Priority-based constitution validation
"""

from typing import List, Dict, Callable, Optional
from .models import (
    StructuredModel,
    ValidationResult,
    GovernanceStatus,
    ConstitutionHook
)


class GovernanceLayer:
    """
    Governance layer with constitution hook registry and validation gauntlet
    Constitutions run in priority order: lowest priority first
    """

    def __init__(self):
        self._constitutions: Dict[int, List[Callable]] = {}  # priority -> list of constitutions
        self._constitution_metadata: Dict[str, Dict] = {}  # name -> metadata

    def attach_constitution(self, constitution: Callable, priority: int) -> None:
        """
        Attach a constitution to the governance layer
        Lower priority = runs first
        """
        if priority not in self._constitutions:
            self._constitutions[priority] = []
        
        self._constitutions[priority].append(constitution)
        
        # Store metadata
        if hasattr(constitution, 'name'):
            self._constitution_metadata[constitution.name] = {
                'version': getattr(constitution, 'version', '1.0.0'),
                'priority': priority
            }

    def detach_constitution(self, constitution_name: str) -> bool:
        """Detach a constitution by name"""
        for priority, constitutions in self._constitutions.items():
            self._constitutions[priority] = [
                c for c in constitutions 
                if getattr(c, 'name', '') != constitution_name
            ]
        
        if constitution_name in self._constitution_metadata:
            del self._constitution_metadata[constitution_name]
            return True
        return False

    def validate(self, model: StructuredModel) -> List[ValidationResult]:
        """
        Run validation gauntlet
        Constitutions run in priority order (lowest first)
        Any BLOCK terminates the gauntlet
        """
        validation_results = []
        
        # Sort by priority (lowest first)
        sorted_priorities = sorted(self._constitutions.keys())
        
        for priority in sorted_priorities:
            for constitution in self._constitutions[priority]:
                result = self._run_constitution(constitution, model)
                validation_results.append(result)
                
                # If BLOCK, terminate gauntlet
                if result.status == GovernanceStatus.BLOCK:
                    break
        
        return validation_results

    def _run_constitution(self, constitution: Callable, model: StructuredModel) -> ValidationResult:
        """Run a single constitution validation"""
        try:
            result = constitution.validate(model)
            
            # Ensure result has required fields
            if not hasattr(result, 'constitution_name'):
                result.constitution_name = getattr(constitution, 'name', 'unknown')
            if not hasattr(result, 'constitution_version'):
                result.constitution_version = getattr(constitution, 'version', '1.0.0')
            if not hasattr(result, 'priority'):
                result.priority = getattr(constitution, 'priority', 999)
                
            return result
        except Exception as e:
            # If constitution fails, return BLOCK result
            return ValidationResult(
                constitution_name=getattr(constitution, 'name', 'unknown'),
                constitution_version=getattr(constitution, 'version', '1.0.0'),
                priority=getattr(constitution, 'priority', 999),
                status=GovernanceStatus.BLOCK,
                violations=[f"Constitution execution error: {str(e)}"],
                warnings=[]
            )

    def get_constitutions(self) -> List[Dict]:
        """Get list of attached constitutions with metadata"""
        constitutions = []
        for priority, const_list in self._constitutions.items():
            for const in const_list:
                constitutions.append({
                    'name': getattr(const, 'name', 'unknown'),
                    'version': getattr(const, 'version', '1.0.0'),
                    'priority': priority
                })
        return sorted(constitutions, key=lambda x: x['priority'])

    def clear_constitutions(self):
        """Clear all attached constitutions"""
        self._constitutions.clear()
        self._constitution_metadata.clear()


# Base constitution class for easy implementation
class BaseConstitution:
    """Base class for constitutions with standard interface"""
    
    name: str = "base_constitution"
    version: str = "1.0.0"
    priority: int = 100

    def validate(self, model: StructuredModel) -> ValidationResult:
        """
        Validate a structured model
        Must return ValidationResult with status, violations, warnings
        """
        raise NotImplementedError("Subclasses must implement validate()")
