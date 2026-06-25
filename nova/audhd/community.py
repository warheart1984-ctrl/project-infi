from __future__ import annotations

from dataclasses import dataclass, field, replace

from nova.audhd.safety_layer import DEFAULT_LOW_STIM, SafetyProfile


def _default_member_profile() -> SafetyProfile:
    return replace(DEFAULT_LOW_STIM)


@dataclass
class MemberProfile:
    id: str
    safety_profile: SafetyProfile = field(default_factory=_default_member_profile)
    preferences: dict = field(default_factory=dict)


@dataclass
class CommunitySpace:
    id: str
    members: dict[str, MemberProfile] = field(default_factory=dict)
    norms: list[str] = field(
        default_factory=lambda: [
            "no forced small talk",
            "no vague criticism",
            "explicit expectations only",
        ]
    )


class AuDHDCommunityKernel:
    def __init__(self) -> None:
        self.spaces: dict[str, CommunitySpace] = {}

    def create_space(self, space_id: str) -> CommunitySpace:
        space = CommunitySpace(id=space_id)
        self.spaces[space_id] = space
        return space

    def add_member(self, space_id: str, member_id: str, profile: MemberProfile) -> None:
        self.spaces[space_id].members[member_id] = profile
