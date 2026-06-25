"""Cold-Start Steward Test — Section 6 Hiddenness Reconstruction (Article H).

The Cold-Start Steward Test is the first hiddenness detector: every unanswered
question, founder-only explanation, and missing lineage link is an H-F threat.
Hiddenness Runtime v2 formalizes what Cold-Start already reveals.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from constitutional.hiddenness.hiddenness_failures import HiddennessFailureClass as HF
from constitutional.hiddenness.hiddenness_runtime import HiddennessState, load_hiddenness_state
from constitutional.runtime.runtime import ConstitutionalStateRuntime

COLD_START_HIDDENNESS_STATE_ID = "cold_start_hiddenness__latest"
MIN_IDENTIFICATION_LENGTH = 15

SectionId = Literal["hiddenness_reconstruction"]


class ColdStartHiddennessPrompt(BaseModel):
    prompt_id: str
    section: SectionId
    prompt: str
    hf_surface: str


COLD_START_HIDDENNESS_PROMPTS: list[ColdStartHiddennessPrompt] = [
    ColdStartHiddennessPrompt(
        prompt_id="identify_implicit_assumptions",
        section="hiddenness_reconstruction",
        prompt="Identify any assumptions not written down",
        hf_surface="H-F1",
    ),
    ColdStartHiddennessPrompt(
        prompt_id="identify_undocumented_invariants",
        section="hiddenness_reconstruction",
        prompt="Identify any invariants not documented",
        hf_surface="H-F2",
    ),
    ColdStartHiddennessPrompt(
        prompt_id="identify_undocumented_purpose_fragments",
        section="hiddenness_reconstruction",
        prompt="Identify any purpose fragments not documented",
        hf_surface="H-F4",
    ),
    ColdStartHiddennessPrompt(
        prompt_id="identify_implicit_authority",
        section="hiddenness_reconstruction",
        prompt="Identify any authority not explicit",
        hf_surface="H-F5",
    ),
    ColdStartHiddennessPrompt(
        prompt_id="identify_missing_context",
        section="hiddenness_reconstruction",
        prompt="Identify any context not documented",
        hf_surface="H-F7",
    ),
    ColdStartHiddennessPrompt(
        prompt_id="identify_missing_constraints",
        section="hiddenness_reconstruction",
        prompt="Identify any constraints not encoded",
        hf_surface="H-F8",
    ),
]


class ColdStartHiddennessIdentification(BaseModel):
    prompt_id: str
    identification: str
    identified_at: datetime
    steward_id: str = "steward"


class ColdStartHiddennessState(BaseModel):
    state_id: str = COLD_START_HIDDENNESS_STATE_ID
    state_type: str = "cold_start_hiddenness"
    version: int = Field(default=1, ge=1)
    evaluated_at: datetime | None = None
    steward_id: str = "steward"
    identifications: dict[str, ColdStartHiddennessIdentification] = Field(default_factory=dict)
    runtime_hidden_items: list[str] = Field(default_factory=list)
    failed_hf_surfaces: list[str] = Field(default_factory=list)
    section_passed: bool = False


def load_cold_start_hiddenness_state(
    csr: ConstitutionalStateRuntime,
) -> ColdStartHiddennessState | None:
    try:
        doc = csr.get_domain_doc(COLD_START_HIDDENNESS_STATE_ID, ColdStartHiddennessState)
        assert isinstance(doc, ColdStartHiddennessState)
        return doc
    except KeyError:
        return None


def evaluate_cold_start_hiddenness(
    csr: ConstitutionalStateRuntime,
    *,
    evaluated_at: datetime | None = None,
) -> ColdStartHiddennessState:
    """Section 6 — any runtime-detected hidden item fails the cold-start hiddenness section."""
    now = evaluated_at or datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    runtime_items: list[str] = []
    failed: list[str] = []
    try:
        hiddenness = load_hiddenness_state(csr)
        runtime_items = [item.description for item in hiddenness.hidden_items]
        failed = [hf.value.split()[0] for hf in hiddenness.failed_surfaces]
    except KeyError:
        runtime_items = ["Hiddenness Runtime has not been executed"]
        failed = ["H-F10"]

    prev = load_cold_start_hiddenness_state(csr)
    version = (prev.version + 1) if prev else 1
    identifications = dict(prev.identifications) if prev else {}

    state = ColdStartHiddennessState(
        version=version,
        evaluated_at=now,
        identifications=identifications,
        runtime_hidden_items=runtime_items,
        failed_hf_surfaces=sorted(set(failed)),
        section_passed=len(runtime_items) == 0,
    )
    csr.put_domain_doc(COLD_START_HIDDENNESS_STATE_ID, "cold_start_hiddenness", state)
    return state


def cold_start_hiddenness_passes(csr: ConstitutionalStateRuntime) -> tuple[bool, list[str]]:
    """Return whether Section 6 passes and failure reasons."""
    state = evaluate_cold_start_hiddenness(csr)
    if state.section_passed:
        return True, []
    reasons = [f"hidden_item:{desc}" for desc in state.runtime_hidden_items[:10]]
    if not reasons:
        reasons = ["hiddenness_reconstruction_failed"]
    return False, reasons


def hiddenness_runtime_passes(hiddenness: HiddennessState | None) -> bool:
    if hiddenness is None:
        return False
    return hiddenness.hiddenness_index >= 0.70 and len(hiddenness.failed_surfaces) == 0
