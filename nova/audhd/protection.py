from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class ProtectionFlags:
    manipulation: bool = False
    overload: bool = False
    boundary_violation: bool = False
    gaslighting_risk: bool = False

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)


class AuDHDProtectionEngine:
    def analyze(self, incoming_text: str) -> ProtectionFlags:
        text = incoming_text.lower()
        flags = ProtectionFlags()

        if "you always" in text or "you never" in text:
            flags.manipulation = True
        if "calm down" in text or "overreacting" in text:
            flags.gaslighting_risk = True
        if text.count("?") + text.count("need you to") > 2:
            flags.overload = True

        return flags

    def apply(self, flags: ProtectionFlags) -> dict[str, bool]:
        actions: dict[str, bool] = {}
        if flags.overload:
            actions["suggest_chunking"] = True
        if flags.manipulation or flags.gaslighting_risk:
            actions["raise_boundary_prompt"] = True
        if flags.boundary_violation:
            actions["raise_boundary_prompt"] = True
        return actions
