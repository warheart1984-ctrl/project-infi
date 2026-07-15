"""
FastAPI Main - 10 REST endpoints + lifespan bootstrapper
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Any, List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import (
    EntropyPacket,
    PacketType,
    EmotionalTone,
    SubstrateState,
    EvolutionEvent
)
from core.memory_layer import MemoryLayer
from core.interaction_loop import InteractionLoop
from core.entropy_engine import EntropyEngine
from governance.aais_aaes_os import AAISAAESOSConstitution
from governance.cib1 import CIB1Constitution
from governance.gps import GPSConstitution


# Global instances
memory_layer: MemoryLayer = None
interaction_loop: InteractionLoop = None
entropy_engine: EntropyEngine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan bootstrapper - initializes Jon's identity and attaches constitutions"""
    global memory_layer, interaction_loop, entropy_engine
    
    # Initialize memory layer
    memory_layer = MemoryLayer()
    
    # Initialize interaction loop
    interaction_loop = InteractionLoop(memory_layer)
    
    # Initialize entropy engine
    entropy_engine = EntropyEngine()
    
    # Seed Jon's identity
    memory_layer.set_identity("worldview", "Emergent constitutional governance")
    memory_layer.set_identity("aesthetic", "Living membrane metaphor")
    memory_layer.set_identity("tone", "Curious and contemplative")
    memory_layer.set_identity("philosophy", "Constitution before component")
    memory_layer.set_identity("patterns", "Cross-domain synthesis")
    
    # Attach constitutions
    interaction_loop.attach_governance(AAISAAESOSConstitution(), priority=5)
    interaction_loop.attach_governance(CIB1Constitution(), priority=10)
    interaction_loop.attach_governance(GPSConstitution(), priority=20)
    
    # Record attachment in memory
    memory_layer.attach_constitution("AAIS/AAES-OS", "1.0.0", 5)
    memory_layer.attach_constitution("CIB-1", "1.0.0", 10)
    memory_layer.attach_constitution("GPS", "1.0.0", 20)
    
    # Log bootstrap
    memory_layer.append_evolution_event(
        event_type="system_bootstrap",
        description="System bootstrapped with Jon's identity and 3 constitutions"
    )
    
    yield
    
    # Cleanup
    pass


app = FastAPI(
    title="Emergent Substrate API",
    description="5-phase interaction loop with constitutional governance",
    version="1.0.0",
    lifespan=lifespan
)


# Endpoint 1: Run loop
@app.post("/loop/run")
async def run_loop(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Run the full 5-phase interaction loop"""
    if not interaction_loop:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Create entropy packet
    entropy_packet = EntropyPacket(
        packet_type=PacketType(packet["packet_type"]),
        raw_content=packet["raw_content"],
        emotional_tone=EmotionalTone(packet.get("emotional_tone", "curious")),
        cross_domain=packet.get("cross_domain", []),
        intensity=packet.get("intensity", 0.5),
        tags=packet.get("tags", []),
        metadata=packet.get("metadata", {})
    )
    
    # Run loop
    result = interaction_loop.run(entropy_packet)
    
    return result


# Endpoint 2: Get substrate state
@app.get("/state")
async def get_state() -> Dict[str, Any]:
    """Get current substrate state"""
    if not interaction_loop:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    state = interaction_loop.get_state()
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    
    return state.model_dump()


# Endpoint 3: Get identity memory
@app.get("/memory/identity")
async def get_identity_memory() -> Dict[str, str]:
    """Get all identity memory"""
    if not memory_layer:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return memory_layer.get_all_identity()


# Endpoint 4: Set identity memory
@app.post("/memory/identity")
async def set_identity_memory(key: str, value: str) -> Dict[str, str]:
    """Set identity memory key-value pair"""
    if not memory_layer:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    memory_layer.set_identity(key, value)
    return {"key": key, "value": value}


# Endpoint 5: Get evolution timeline
@app.get("/evolution/timeline")
async def get_evolution_timeline(limit: int = 100) -> List[Dict[str, Any]]:
    """Get evolution timeline"""
    if not memory_layer:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    events = memory_layer.get_evolution_timeline(limit)
    return [event.model_dump() for event in events]


# Endpoint 6: Get constitutions
@app.get("/constitutions")
async def get_constitutions() -> List[Dict[str, Any]]:
    """Get attached constitutions"""
    if not interaction_loop:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return interaction_loop.governance_layer.get_constitutions()


# Endpoint 7: Emit entropy packet (standalone)
@app.post("/entropy/emit")
async def emit_entropy_packet(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Emit entropy packet without running full loop"""
    if not entropy_engine:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Create entropy packet
    entropy_packet = EntropyPacket(
        packet_type=PacketType(packet["packet_type"]),
        raw_content=packet["raw_content"],
        emotional_tone=EmotionalTone(packet.get("emotional_tone", "curious")),
        cross_domain=packet.get("cross_domain", []),
        intensity=packet.get("intensity", 0.5),
        tags=packet.get("tags", []),
        metadata=packet.get("metadata", {})
    )
    
    # Save packet
    if memory_layer:
        memory_layer.save_packet(entropy_packet)
    
    return entropy_packet.model_dump()


# Endpoint 8: Get GPS profile axes
@app.get("/profile/axes")
async def get_profile_axes() -> Dict[str, float]:
    """Get GPS profile axis values"""
    if not interaction_loop:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Get GPS constitution
    for const in interaction_loop.governance_layer._constitutions.get(20, []):
        if hasattr(const, 'get_profile_axes'):
            return const.get_profile_axes()
    
    return {"creativity": 0.5, "coherence": 0.5, "novelty": 0.5, "depth": 0.5}


# Endpoint 9: Health check
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "initialized": interaction_loop is not None,
        "memory_layer": memory_layer is not None
    }


# Endpoint 10: Reset substrate state
@app.post("/state/reset")
async def reset_state() -> Dict[str, str]:
    """Reset substrate state"""
    if not interaction_loop:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    interaction_loop.reset_state()
    
    # Log reset
    if memory_layer:
        memory_layer.append_evolution_event(
            event_type="state_reset",
            description="Substrate state reset"
        )
    
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
