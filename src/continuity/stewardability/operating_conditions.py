"""Stewardability Operating Conditions — when steward generation can actually emerge."""

from __future__ import annotations

from pydantic import BaseModel


class EpistemicConditions(BaseModel):
    history_accessible: bool = False
    registers_complete_enough: bool = False
    failures_visible: bool = False
    reasoning_transparent: bool = False


class EnvironmentalConditions(BaseModel):
    novelty_available: bool = False
    conflict_present: bool = False
    uncertainty_non_trivial: bool = False


class SocialConditions(BaseModel):
    principled_disagreement_safe: bool = False
    critique_rewarded: bool = False
    conformity_not_over_rewarded: bool = False


class InstitutionalConditions(BaseModel):
    authority_by_stewardship: bool = False
    succession_tests_enforced: bool = False
    gatekeeping_limited: bool = False


class StewardabilityConditions(BaseModel):
    epistemic: EpistemicConditions = EpistemicConditions()
    environmental: EnvironmentalConditions = EnvironmentalConditions()
    social: SocialConditions = SocialConditions()
    institutional: InstitutionalConditions = InstitutionalConditions()


def is_stewardability_viable(conditions: StewardabilityConditions) -> bool:
    return (
        conditions.epistemic.history_accessible
        and conditions.epistemic.reasoning_transparent
        and conditions.environmental.novelty_available
        and conditions.environmental.uncertainty_non_trivial
        and conditions.social.principled_disagreement_safe
        and conditions.social.critique_rewarded
        and conditions.institutional.authority_by_stewardship
        and conditions.institutional.succession_tests_enforced
    )


def good_conditions() -> StewardabilityConditions:
    return StewardabilityConditions(
        epistemic=EpistemicConditions(
            history_accessible=True,
            registers_complete_enough=True,
            failures_visible=True,
            reasoning_transparent=True,
        ),
        environmental=EnvironmentalConditions(
            novelty_available=True,
            conflict_present=True,
            uncertainty_non_trivial=True,
        ),
        social=SocialConditions(
            principled_disagreement_safe=True,
            critique_rewarded=True,
            conformity_not_over_rewarded=True,
        ),
        institutional=InstitutionalConditions(
            authority_by_stewardship=True,
            succession_tests_enforced=True,
            gatekeeping_limited=True,
        ),
    )


def bad_conditions() -> StewardabilityConditions:
    return StewardabilityConditions(
        epistemic=EpistemicConditions(
            history_accessible=True,
            registers_complete_enough=True,
            failures_visible=False,
            reasoning_transparent=False,
        ),
        environmental=EnvironmentalConditions(
            novelty_available=False,
            conflict_present=False,
            uncertainty_non_trivial=False,
        ),
        social=SocialConditions(
            principled_disagreement_safe=False,
            critique_rewarded=False,
            conformity_not_over_rewarded=False,
        ),
        institutional=InstitutionalConditions(
            authority_by_stewardship=False,
            succession_tests_enforced=False,
            gatekeeping_limited=False,
        ),
    )
