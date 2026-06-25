"""Tier 0 cosmic-ray / spectrum receiver types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import numpy as np


@dataclass
class CosmicRayData:
    energy: Optional[np.ndarray] = None
    flux: Optional[np.ndarray] = None
    timestamp: Optional[str] = None
    quality: Optional[Dict[str, Any]] = None
    concentration_10be_equiv: Optional[float] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
