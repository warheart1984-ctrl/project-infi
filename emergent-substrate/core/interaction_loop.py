"""
Interaction Loop - 5-phase loop
INPUT → STABILIZATION → VALIDATION → FEEDBACK → INTEGRATE
"""

from typing import Optional, Callable, Dict, Any
from .models import (
    EntropyPacket,
    StructuredModel,
    GovernedSpec,
    SubstrateState,
    EvolutionEvent,
    GovernanceStatus
)
from .entropy_engine import EntropyEngine
from .order_engine import OrderEngine
from .memory_layer import MemoryLayer
from .governance_layer import GovernanceLayer


class InteractionLoop:
    """
    5-phase interaction loop
    1. INPUT - Entropy packet persisted
    2. STABILIZATION - OrderEngine.shape() → StructuredModel
    3. VALIDATION - GovernanceLayer.validate() → PASS/WARN/BLOCK
    4. FEEDBACK - Optional feedback hook fires
    5. INTEGRATION - OrderEngine.integrate() → MemoryLayer
    """

    def __init__(self, memory_layer: MemoryLayer):
        self.memory_layer = memory_layer
        self.entropy_engine = EntropyEngine()
        self.order_engine = OrderEngine()
        self.governance_layer = GovernanceLayer()
        
        self.feedback_hook: Optional[Callable] = None
        self.iteration_count = 0
        self.state: Optional[SubstrateState] = None

    def attach_governance(self, constitution: Callable, priority: int) -> None:
        """Attach a constitution to the governance layer"""
        self.governance_layer.attach_constitution(constitution, priority)

    def attach_feedback_hook(self, hook: Callable) -> None:
        """Attach a feedback hook for phase 4"""
        self.feedback_hook = hook

    def run(
        self,
        packet: EntropyPacket
    ) -> Dict[str, Any]:
        """
        Run the full 5-phase interaction loop
        Returns loop result with governance status and integration status
        """
        self.iteration_count += 1
        
        # Phase 1: INPUT - Persist entropy packet
        self.memory_layer.save_packet(packet)
        self.memory_layer.append_evolution_event(
            event_type="packet_emitted",
            description=f"Emitted {packet.packet_type.value} packet",
            related_ids=[packet.packet_id]
        )
        
        # Phase 2: STABILIZATION - Shape into structured model
        model = self.order_engine.shape(packet)
        self.memory_layer.save_model(model)
        
        # Phase 3: VALIDATION - Governance gauntlet
        validation_results = self.governance_layer.validate(model)
        
        # Save validation results
        for result in validation_results:
            self.memory_layer.save_validation_result(result, model.model_id)
        
        # Determine overall governance status
        overall_status = self._determine_overall_status(validation_results)
        
        # Govern the spec
        spec = self.order_engine.govern(model, validation_results)
        self.memory_layer.save_spec(spec)
        
        # Phase 4: FEEDBACK - Optional feedback hook
        if self.feedback_hook and overall_status != GovernanceStatus.BLOCK:
            try:
                feedback_result = self.feedback_hook(packet, model, spec, validation_results)
                if feedback_result:
                    self.memory_layer.append_evolution_event(
                        event_type="feedback_hook_fired",
                        description=f"Feedback hook: {feedback_result}",
                        related_ids=[packet.packet_id, model.model_id, spec.spec_id]
                    )
            except Exception as e:
                # Log error but don't fail the loop
                self.memory_layer.append_evolution_event(
                    event_type="feedback_hook_error",
                    description=f"Feedback hook error: {str(e)}",
                    related_ids=[packet.packet_id]
                )
        
        # Phase 5: INTEGRATION - Integrate if governance passed
        integrated = False
        if overall_status != GovernanceStatus.BLOCK:
            self.order_engine.integrate(spec, self.memory_layer)
            integrated = True
        else:
            self.memory_layer.append_evolution_event(
                event_type="spec_blocked",
                description=f"Spec blocked by governance: {spec.title}",
                related_ids=[spec.spec_id, model.model_id]
            )
        
        # Update substrate state
        self._update_state(packet, spec, integrated)
        
        # Return loop result
        return {
            "iteration": self.iteration_count,
            "packet_id": packet.packet_id,
            "model_id": model.model_id,
            "spec_id": spec.spec_id,
            "governance_status": overall_status.value,
            "spec_title": spec.title,
            "integrated": integrated,
            "is_alive": self.state.is_alive if self.state else False,
            "validation_results": [r.model_dump() for r in validation_results]
        }

    def _determine_overall_status(self, validation_results) -> GovernanceStatus:
        """Determine overall governance status from validation results"""
        if any(r.status == GovernanceStatus.BLOCK for r in validation_results):
            return GovernanceStatus.BLOCK
        elif any(r.status == GovernanceStatus.WARN for r in validation_results):
            return GovernanceStatus.WARN
        return GovernanceStatus.PASS

    def _update_state(self, packet: EntropyPacket, spec: GovernedSpec, integrated: bool):
        """Update substrate state after loop iteration"""
        # Get existing state or create new
        if not self.state:
            self.state = SubstrateState()
        
        # Update counters
        self.state.iteration = self.iteration_count
        self.state.total_packets_emitted += 1
        if integrated:
            self.state.total_specs_produced += 1
        self.state.total_loop_iterations += 1
        
        # Update constitution count
        constitutions = self.memory_layer.get_constitutions()
        self.state.total_constitutions_attached = len(constitutions)
        
        # Check if identity memory is non-empty
        identity = self.memory_layer.get_all_identity()
        self.state.identity_memory_non_empty = len(identity) > 0
        
        # Update last activity
        from datetime import datetime
        self.state.last_activity = datetime.utcnow()
        
        # Check if alive
        self.state.is_alive = self.state.check_alive()
        
        # Save state
        self.memory_layer.save_state(self.state)

    def get_state(self) -> Optional[SubstrateState]:
        """Get current substrate state"""
        return self.state

    def reset_state(self):
        """Reset substrate state"""
        self.state = None
        self.iteration_count = 0
