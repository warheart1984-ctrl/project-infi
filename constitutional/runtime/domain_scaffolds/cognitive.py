"""Cognitive runtime — state documents and receipt kinds."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RUNTIME_NAME = "CognitiveRuntime"

QuestionStatus = Literal["open", "resolved"]
InsightReceiptKind = Literal["Discovery", "Refinement", "Invalidation"]
HypothesisReceiptKind = Literal["Propose", "Test", "Confirm", "Reject"]
ModelReceiptKind = Literal["Adopt", "Update", "Retire"]


class InsightStateDoc(BaseModel):
    state_type: Literal["InsightState"] = "InsightState"
    insight_id: str
    statement: str
    source: str
    linked_decisions: list[str] = Field(default_factory=list)


class QuestionStateDoc(BaseModel):
    state_type: Literal["QuestionState"] = "QuestionState"
    question_id: str
    status: QuestionStatus = "open"
    importance: str = "normal"
    statement: str = ""


class HypothesisStateDoc(BaseModel):
    state_type: Literal["HypothesisState"] = "HypothesisState"
    hypothesis_id: str
    statement: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    status: str = "proposed"


class MentalModelStateDoc(BaseModel):
    state_type: Literal["MentalModelState"] = "MentalModelState"
    model_id: str
    name: str
    version: str = "1"
    scope: str = ""
    superseded_by: str | None = None


class DecisionPatternStateDoc(BaseModel):
    state_type: Literal["DecisionPatternState"] = "DecisionPatternState"
    pattern_id: str
    description: str
    conditions: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)
