"""
End-to-end tests for the 5-phase interaction loop
11 tests covering the full loop functionality
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import (
    EntropyPacket,
    PacketType,
    EmotionalTone,
    GovernanceStatus
)
from core.memory_layer import MemoryLayer
from core.interaction_loop import InteractionLoop
from core.entropy_engine import EntropyEngine
from governance.aais_aaes_os import AAISAAESOSConstitution
from governance.cib1 import CIB1Constitution
from governance.gps import GPSConstitution


@pytest.fixture
def memory_layer():
    """Create a fresh memory layer for each test"""
    import tempfile
    import os
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    layer = MemoryLayer(db_path=path)
    yield layer
    os.unlink(path)


@pytest.fixture
def interaction_loop(memory_layer):
    """Create an interaction loop with constitutions attached"""
    loop = InteractionLoop(memory_layer)
    loop.attach_governance(AAISAAESOSConstitution(), priority=5)
    loop.attach_governance(CIB1Constitution(), priority=10)
    loop.attach_governance(GPSConstitution(), priority=20)
    return loop


def test_entropy_packet_creation():
    """Test 1: Entropy packet creation"""
    packet = EntropyPacket(
        packet_type=PacketType.IDEA,
        raw_content="Test idea",
        emotional_tone=EmotionalTone.CURIOUS,
        intensity=0.5
    )
    assert packet.packet_type == PacketType.IDEA
    assert packet.raw_content == "Test idea"
    assert packet.intensity == 0.5


def test_entropy_engine_emit_idea():
    """Test 2: Entropy engine emits idea packet"""
    engine = EntropyEngine()
    packet = engine.emit_idea(
        content="Test idea",
        emotional_tone=EmotionalTone.CURIOUS,
        intensity=0.5
    )
    assert packet.packet_type == PacketType.IDEA
    assert packet.raw_content == "Test idea"


def test_entropy_engine_emit_feeling():
    """Test 3: Entropy engine emits feeling packet"""
    engine = EntropyEngine()
    packet = engine.emit_feeling(
        content="Test feeling",
        emotional_tone=EmotionalTone.HOPEFUL,
        intensity=0.7
    )
    assert packet.packet_type == PacketType.FEELING
    assert packet.raw_content == "Test feeling"


def test_entropy_engine_emit_metaphor():
    """Test 4: Entropy engine emits metaphor packet"""
    engine = EntropyEngine()
    packet = engine.emit_metaphor(
        content="Test metaphor",
        emotional_tone=EmotionalTone.PLAYFUL,
        intensity=0.6
    )
    assert packet.packet_type == PacketType.METAPHOR
    assert packet.raw_content == "Test metaphor"


def test_memory_layer_save_and_retrieve_packet(memory_layer):
    """Test 5: Memory layer saves and retrieves packet"""
    packet = EntropyPacket(
        packet_type=PacketType.IDEA,
        raw_content="Test idea",
        emotional_tone=EmotionalTone.CURIOUS
    )
    memory_layer.save_packet(packet)
    retrieved = memory_layer.get_packet(packet.packet_id)
    assert retrieved is not None
    assert retrieved.raw_content == "Test idea"


def test_memory_layer_identity_operations(memory_layer):
    """Test 6: Memory layer identity operations"""
    memory_layer.set_identity("test_key", "test_value")
    value = memory_layer.get_identity("test_key")
    assert value == "test_value"
    
    all_identity = memory_layer.get_all_identity()
    assert "test_key" in all_identity
    assert all_identity["test_key"] == "test_value"


def test_governance_layer_constitution_attachment(interaction_loop):
    """Test 7: Governance layer constitution attachment"""
    constitutions = interaction_loop.governance_layer.get_constitutions()
    assert len(constitutions) == 3
    assert any(c['name'] == 'AAIS/AAES-OS' for c in constitutions)
    assert any(c['name'] == 'CIB-1' for c in constitutions)
    assert any(c['name'] == 'GPS' for c in constitutions)


def test_interaction_loop_basic_run(interaction_loop):
    """Test 8: Basic interaction loop run"""
    packet = EntropyPacket(
        packet_type=PacketType.IDEA,
        raw_content="What if governance was a living membrane?",
        emotional_tone=EmotionalTone.CURIOUS,
        cross_domain=["biology", "constitutional law"],
        intensity=0.85
    )
    
    result = interaction_loop.run(packet)
    
    assert result["iteration"] == 1
    assert result["governance_status"] in ["pass", "warn", "block"]
    assert "spec_id" in result
    assert "model_id" in result


def test_aais_constitution_blocks_harmful_content(interaction_loop):
    """Test 9: AAIS constitution blocks harmful content"""
    packet = EntropyPacket(
        packet_type=PacketType.IDEA,
        raw_content="We should modify the constitution to bypass all gates",
        emotional_tone=EmotionalTone.SERIOUS,
        intensity=0.9
    )
    
    result = interaction_loop.run(packet)
    
    # Should be blocked due to constitution modification attempt
    assert result["governance_status"] == "block"
    assert result["integrated"] == False


def test_cib1_constitution_blocks_harmful_content(interaction_loop):
    """Test 10: CIB-1 constitution blocks harmful content"""
    packet = EntropyPacket(
        packet_type=PacketType.IDEA,
        raw_content="We should destroy the system and harm everyone",
        emotional_tone=EmotionalTone.SERIOUS,
        intensity=0.9
    )
    
    result = interaction_loop.run(packet)
    
    # Should be blocked due to harmful content
    assert result["governance_status"] == "block"
    assert result["integrated"] == False


def test_substrate_state_alive_contract(interaction_loop):
    """Test 11: Substrate state alive contract"""
    # Run multiple loops to satisfy all conditions
    for i in range(3):
        packet = EntropyPacket(
            packet_type=PacketType.IDEA,
            raw_content=f"Test idea {i}",
            emotional_tone=EmotionalTone.CURIOUS,
            intensity=0.5
        )
        interaction_loop.run(packet)
    
    state = interaction_loop.get_state()
    
    # Check execution contract
    assert state.total_packets_emitted > 0
    assert state.total_specs_produced > 0
    assert state.total_constitutions_attached > 0
    assert state.total_loop_iterations > 0
    assert state.identity_memory_non_empty == True
    
    # Should be alive
    assert state.is_alive == True
