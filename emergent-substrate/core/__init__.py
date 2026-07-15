"""
Emergent Substrate - Core Module
A 5-phase interaction loop with constitutional governance
"""

from .models import (
    EntropyPacket,
    StructuredModel,
    GovernedSpec,
    SubstrateState,
    EvolutionEvent,
    ValidationResult,
    PacketType,
    EmotionalTone,
    GovernanceStatus
)
from .entropy_engine import EntropyEngine
from .order_engine import OrderEngine
from .memory_layer import MemoryLayer
from .governance_layer import GovernanceLayer
from .interaction_loop import InteractionLoop

__all__ = [
    # Models
    "EntropyPacket",
    "StructuredModel",
    "GovernedSpec",
    "SubstrateState",
    "EvolutionEvent",
    "ValidationResult",
    "PacketType",
    "EmotionalTone",
    "GovernanceStatus",
    # Engines
    "EntropyEngine",
    "OrderEngine",
    # Layers
    "MemoryLayer",
    "GovernanceLayer",
    # Loop
    "InteractionLoop",
]

__version__ = "1.0.0"
