from __future__ import annotations

from typing import Dict

GLOBAL_CAPABILITY_HARD_CAP = 10

DOMAIN_LADDERS: Dict[str, dict] = {
    "cognition": {"max_level": 10, "base_step": 1.0},
    "planning": {"max_level": 10, "base_step": 1.0},
    "governance": {"max_level": 8, "base_step": 0.5},
    "substrate": {"max_level": 6, "base_step": 0.3},
}


def next_capability(domain: str, current: int, delta: float) -> int:
    cfg = DOMAIN_LADDERS.get(domain, {"max_level": 10, "base_step": 1.0})
    step = cfg["base_step"] * delta
    new_level = int(round(current + step))
    domain_max = min(int(cfg["max_level"]), GLOBAL_CAPABILITY_HARD_CAP)
    return max(1, min(new_level, domain_max))
