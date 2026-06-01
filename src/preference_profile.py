# src/preference_profile.py

from dataclasses import dataclass, field
from typing import List, Optional
from src.performance import timed
from src.logger import get_logger

logger = get_logger(__name__)

@dataclass
class MusicPreferenceProfile:
    user_id: str
    genres: List[str] = field(default_factory=list)
    energy_level: str = "moderate"  # calm, moderate, high
    vocals: bool = False
    liked_artists: List[str] = field(default_factory=list)
    disliked_styles: List[str] = field(default_factory=list)
    feedback_history: List[dict] = field(default_factory=list)

    def to_composition_params(self, stress_level: float) -> dict:
        """Convert profile + current stress into composition parameters"""
        base_tempo = {
            "calm": 60,
            "moderate": 90,
            "high": 120
        }.get(self.energy_level, 90)

        # Stress adjusts tempo down
        adjusted_tempo = base_tempo * (1 - (stress_level * 0.3))

        return {
            "tempo": round(adjusted_tempo),
            "genres": self.genres,
            "vocals": self.vocals,
            "energy": self.energy_level,
            "stress_modifier": stress_level
        }

    def record_feedback(self, params: dict, liked: bool):
        """Store feedback for future refinement"""
        self.feedback_history.append({
            "params": params,
            "liked": liked
        })
        logger.info(f"Feedback recorded: {'liked' if liked else 'disliked'}")