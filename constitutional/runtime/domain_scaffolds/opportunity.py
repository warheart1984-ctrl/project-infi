"""Opportunity runtime — state documents and receipt kinds."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RUNTIME_NAME = "OpportunityRuntime"

OpportunityReceiptKind = Literal["Discover", "Qualify", "Advance", "Win", "Lose", "Abandon"]
DependencyReceiptKind = Literal["Add", "Resolve", "Fail"]


class OpportunityStateDoc(BaseModel):
    state_type: Literal["OpportunityState"] = "OpportunityState"
    opportunity_id: str
    description: str
    value: float = 0.0
    probability: float = Field(default=0.5, ge=0.0, le=1.0)
    decay_curve: str = "linear"
    deadline: str | None = None
    status: str = "open"


class DependencyStateDoc(BaseModel):
    state_type: Literal["DependencyState"] = "DependencyState"
    dependency_id: str
    type: str
    status: str = "open"
    blocks_opportunities: list[str] = Field(default_factory=list)


class OpportunityPortfolioStateDoc(BaseModel):
    state_type: Literal["OpportunityPortfolioState"] = "OpportunityPortfolioState"
    portfolio_id: str
    opportunity_ids: list[str] = Field(default_factory=list)
    risk_profile: str = "balanced"
