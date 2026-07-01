from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class IdentityType(str, Enum):
    AGENT = "agent"
    MODEL = "model"
    OPERATOR = "operator"


@dataclass
class Identity:
    id: str
    type: IdentityType
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    id: str
    run_id: str
    type: str
    timestamp: int
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Receipt:
    run_id: str
    hash: str
    spans: List[Span]
    result: Any
    created_at: str
