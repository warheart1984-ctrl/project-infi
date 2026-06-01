from __future__ import annotations

from typing import Protocol

from story_forge.contracts.cinematic import CinematicLaneInput, CinematicPlan
from story_forge.contracts.directional import DirectionalContext, DirectionalLaneInput
from story_forge.contracts.presentation import PresentationLaneInput, PresentedOutput
from story_forge.contracts.staging import StagedPlan, StagingLaneInput
from story_forge.contracts.translation import SceneGrammar, TranslationLaneInput


class TranslationLaneProtocol(Protocol):
    def run(self, lane_input: TranslationLaneInput) -> SceneGrammar: ...


class StagingLaneProtocol(Protocol):
    def run(self, lane_input: StagingLaneInput) -> StagedPlan: ...


class DirectionalLaneProtocol(Protocol):
    def run(self, lane_input: DirectionalLaneInput) -> DirectionalContext: ...


class PresentationLaneProtocol(Protocol):
    def run(self, lane_input: PresentationLaneInput) -> PresentedOutput: ...


class CinematicLaneProtocol(Protocol):
    def run(self, lane_input: CinematicLaneInput) -> CinematicPlan: ...
