"""
Entropy Engine - Jon's side
Emits: idea, feeling, metaphor, challenge, extension, mutation
"""

from typing import Optional
from .models import EntropyPacket, PacketType, EmotionalTone


class EntropyEngine:
    """
    Jon's entropy emission engine
    Generates raw entropy packets across multiple modalities
    """

    def emit_idea(
        self,
        content: str,
        emotional_tone: EmotionalTone = EmotionalTone.CURIOUS,
        cross_domain: Optional[list] = None,
        intensity: float = 0.5,
        tags: Optional[list] = None,
        metadata: Optional[dict] = None
    ) -> EntropyPacket:
        """Emit an idea packet"""
        return EntropyPacket(
            packet_type=PacketType.IDEA,
            raw_content=content,
            emotional_tone=emotional_tone,
            cross_domain=cross_domain or [],
            intensity=intensity,
            tags=tags or [],
            metadata=metadata or {}
        )

    def emit_feeling(
        self,
        content: str,
        emotional_tone: EmotionalTone = EmotionalTone.NEUTRAL,
        intensity: float = 0.5,
        tags: Optional[list] = None,
        metadata: Optional[dict] = None
    ) -> EntropyPacket:
        """Emit a feeling packet"""
        return EntropyPacket(
            packet_type=PacketType.FEELING,
            raw_content=content,
            emotional_tone=emotional_tone,
            cross_domain=[],
            intensity=intensity,
            tags=tags or [],
            metadata=metadata or {}
        )

    def emit_metaphor(
        self,
        content: str,
        emotional_tone: EmotionalTone = EmotionalTone.PLAYFUL,
        cross_domain: Optional[list] = None,
        intensity: float = 0.5,
        tags: Optional[list] = None,
        metadata: Optional[dict] = None
    ) -> EntropyPacket:
        """Emit a metaphor packet"""
        return EntropyPacket(
            packet_type=PacketType.METAPHOR,
            raw_content=content,
            emotional_tone=emotional_tone,
            cross_domain=cross_domain or [],
            intensity=intensity,
            tags=tags or [],
            metadata=metadata or {}
        )

    def emit_challenge(
        self,
        content: str,
        emotional_tone: EmotionalTone = EmotionalTone.SERIOUS,
        cross_domain: Optional[list] = None,
        intensity: float = 0.7,
        tags: Optional[list] = None,
        metadata: Optional[dict] = None
    ) -> EntropyPacket:
        """Emit a challenge packet"""
        return EntropyPacket(
            packet_type=PacketType.CHALLENGE,
            raw_content=content,
            emotional_tone=emotional_tone,
            cross_domain=cross_domain or [],
            intensity=intensity,
            tags=tags or [],
            metadata=metadata or {}
        )

    def emit_extension(
        self,
        content: str,
        emotional_tone: EmotionalTone = EmotionalTone.EXCITED,
        cross_domain: Optional[list] = None,
        intensity: float = 0.6,
        tags: Optional[list] = None,
        metadata: Optional[dict] = None
    ) -> EntropyPacket:
        """Emit an extension packet"""
        return EntropyPacket(
            packet_type=PacketType.EXTENSION,
            raw_content=content,
            emotional_tone=emotional_tone,
            cross_domain=cross_domain or [],
            intensity=intensity,
            tags=tags or [],
            metadata=metadata or {}
        )

    def emit_mutation(
        self,
        content: str,
        emotional_tone: EmotionalTone = EmotionalTone.CURIOUS,
        cross_domain: Optional[list] = None,
        intensity: float = 0.8,
        tags: Optional[list] = None,
        metadata: Optional[dict] = None
    ) -> EntropyPacket:
        """Emit a mutation packet"""
        return EntropyPacket(
            packet_type=PacketType.MUTATION,
            raw_content=content,
            emotional_tone=emotional_tone,
            cross_domain=cross_domain or [],
            intensity=intensity,
            tags=tags or [],
            metadata=metadata or {}
        )
