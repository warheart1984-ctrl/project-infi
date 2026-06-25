"""CSR bridge registration for domain state documents."""

from __future__ import annotations

from datetime import UTC, datetime

from constitutional.runtime import ConstitutionalStateRuntime
from constitutional.runtime.csr_bridge import register_domain_state, state_id_from_doc
from constitutional.runtime.personal_continuity_runtime import IdeaState


def test_idea_state_registers_with_csr() -> None:
    csr = ConstitutionalStateRuntime()
    doc = IdeaState(
        state_id="idea-1",
        title="Collapse the stack",
        status="seed",
        last_updated_at=datetime.now(UTC),
    )
    assert state_id_from_doc(doc) == "idea-1"
    state = register_domain_state(csr, doc, runtime_key="personal_continuity")
    assert state.state_type == "idea"
    assert "PC-1" in state.invariants
    assert csr.get_state("idea-1").current_state == "Proposed"
    stored = csr.get_domain_doc("idea-1", IdeaState)
    assert stored.title == "Collapse the stack"
