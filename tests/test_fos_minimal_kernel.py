"""FOS v0.1 minimal kernel tests."""

from __future__ import annotations

import pytest

from src.continuity.cab import CABLedger, DecisionRecord, EvidenceChain, IntentRecord
from src.fos import EventType, FOSKernel, FOSMemoryObject, FileStore, validate_memory_object


@pytest.fixture
def kernel() -> FOSKernel:
    return FOSKernel()


@pytest.fixture
def decision_thread(kernel: FOSKernel):
    thread = kernel.create_thread("NeoMundi Architecture Choice")
    note = kernel.append_event(thread.id, EventType.NOTE, {"text": "Need governed world model."})
    evidence = kernel.append_event(
        thread.id,
        EventType.EVIDENCE,
        {"source": "experiment", "summary": "Ungoverned agents drift."},
        [note.id],
    )
    architecture = kernel.append_event(
        thread.id,
        EventType.ARCHITECTURE,
        {
            "name": "NeoMundi v1",
            "version": "v1",
            "definition": "governed world model over FOS",
            "evidence_refs": [evidence.id],
        },
        [note.id, evidence.id],
    )
    governance = kernel.append_event(
        thread.id,
        EventType.GOVERNANCE,
        {
            "name": "FOS law",
            "authority_scope": "memory",
            "definition": "all objects require evidence and lineage",
            "evidence_refs": [evidence.id],
        },
        [evidence.id],
    )
    decision = kernel.append_event(
        thread.id,
        EventType.DECISION,
        {
            "title": "Adopt NeoMundi v1",
            "rationale": "FOS continuity is needed.",
            "chosen_architecture": architecture.id,
            "evidence_refs": [evidence.id],
            "governance_refs": [governance.id],
        },
        [architecture.id, evidence.id, governance.id],
    )
    outcome = kernel.append_event(
        thread.id,
        EventType.NOTE,
        {"text": "Decision accepted as continuity substrate view."},
        [decision.id],
    )
    return kernel, thread, note, evidence, architecture, governance, decision, outcome


def test_create_thread_has_continuity_id(kernel: FOSKernel):
    thread = kernel.create_thread("Founder Memory")
    assert thread.id.startswith("thread:")
    assert kernel.get_thread(thread.id) == thread


def test_create_child_thread_requires_parent(kernel: FOSKernel):
    parent = kernel.create_thread("parent")
    child = kernel.create_thread("child", parent=parent.id)
    assert child.parent == parent.id


def test_missing_parent_thread_fails(kernel: FOSKernel):
    with pytest.raises(ValueError, match="parent thread"):
        kernel.create_thread("child", parent="thread:missing")


def test_append_event_requires_existing_thread(kernel: FOSKernel):
    with pytest.raises(ValueError, match="thread does not exist"):
        kernel.append_event("thread:nope", EventType.NOTE, {"text": "x"})


def test_append_event_records_payload_and_type(kernel: FOSKernel):
    thread = kernel.create_thread("t")
    event = kernel.append_event(thread.id, EventType.CONCEPT, {"definition": "d"})
    assert event.event_type == EventType.CONCEPT
    assert event.payload["definition"] == "d"


def test_append_event_rejects_missing_lineage(kernel: FOSKernel):
    thread = kernel.create_thread("t")
    with pytest.raises(ValueError, match="lineage event"):
        kernel.append_event(thread.id, EventType.DECISION, {"rationale": "r"}, ["event:missing"])


def test_list_events_for_thread_is_timestamp_ordered(decision_thread):
    kernel, thread, *_ = decision_thread
    events = kernel.list_events_for_thread(thread.id)
    assert [event.timestamp for event in events] == sorted(event.timestamp for event in events)


def test_lineage_chain_is_root_first(kernel: FOSKernel):
    thread = kernel.create_thread("t")
    root = kernel.append_event(thread.id, EventType.NOTE, {"text": "root"})
    middle = kernel.append_event(thread.id, EventType.EVIDENCE, {"summary": "middle"}, [root.id])
    leaf = kernel.append_event(thread.id, EventType.DECISION, {"rationale": "leaf"}, [middle.id])
    assert [event.id for event in kernel.get_lineage_chain(leaf.id)] == [root.id, middle.id, leaf.id]


def test_lineage_chain_dedupes_diamond(kernel: FOSKernel):
    thread = kernel.create_thread("t")
    root = kernel.append_event(thread.id, EventType.NOTE, {"text": "root"})
    a = kernel.append_event(thread.id, EventType.EVIDENCE, {"summary": "a"}, [root.id])
    b = kernel.append_event(thread.id, EventType.GOVERNANCE, {"definition": "b"}, [root.id])
    c = kernel.append_event(thread.id, EventType.DECISION, {"rationale": "c"}, [a.id, b.id])
    chain = kernel.get_lineage_chain(c.id)
    assert [event.id for event in chain].count(root.id) == 1


def test_memory_ref_uses_event_type(kernel: FOSKernel):
    thread = kernel.create_thread("t")
    event = kernel.append_event(thread.id, EventType.EVIDENCE, {"summary": "s"})
    ref = kernel.memory_ref(event.id)
    assert ref.event_id == event.id
    assert ref.event_type == EventType.EVIDENCE


def test_memory_ref_missing_event_fails(kernel: FOSKernel):
    with pytest.raises(ValueError, match="event does not exist"):
        kernel.memory_ref("event:nope")


def test_evidence_event_validates_as_memory_object(kernel: FOSKernel):
    thread = kernel.create_thread("t")
    event = kernel.append_event(thread.id, EventType.EVIDENCE, {"summary": "s"})
    obj = kernel.memory_object_from_event(event)
    assert validate_memory_object(obj) == []


def test_decision_without_lineage_fails_memory_invariant(kernel: FOSKernel):
    thread = kernel.create_thread("t")
    event = kernel.append_event(thread.id, EventType.DECISION, {"rationale": "r", "evidence_refs": ["ev"]})
    assert "missing lineage" in kernel.validate_event_as_memory_object(event.id)


def test_memory_object_requires_id():
    obj = FOSMemoryObject("", "Concept", "d", ["e"], ["l"], "v1", "thread")
    assert "missing id" in validate_memory_object(obj)


def test_memory_object_requires_type():
    obj = FOSMemoryObject("id", "", "d", ["e"], ["l"], "v1", "thread")
    assert "missing type" in validate_memory_object(obj)


def test_memory_object_requires_definition():
    obj = FOSMemoryObject("id", "Concept", "", ["e"], ["l"], "v1", "thread")
    assert "missing definition" in validate_memory_object(obj)


def test_memory_object_requires_evidence():
    obj = FOSMemoryObject("id", "Concept", "d", [], ["l"], "v1", "thread")
    assert "missing evidence_refs" in validate_memory_object(obj)


def test_memory_object_requires_lineage():
    obj = FOSMemoryObject("id", "Concept", "d", ["e"], [], "v1", "thread")
    assert "missing lineage" in validate_memory_object(obj)


def test_memory_object_requires_version():
    obj = FOSMemoryObject("id", "Concept", "d", ["e"], ["l"], "", "thread")
    assert "missing version" in validate_memory_object(obj)


def test_memory_object_requires_continuity_thread():
    obj = FOSMemoryObject("id", "Concept", "d", ["e"], ["l"], "v1", "")
    assert "missing continuity_thread" in validate_memory_object(obj)


def test_reconstruct_decision_classifies_lineage(decision_thread):
    kernel, thread, note, evidence, architecture, governance, decision, outcome = decision_thread
    reconstruction = kernel.reconstruct_decision(decision.id)
    assert reconstruction.thread.id == thread.id
    assert [event.id for event in reconstruction.discussion_events] == [note.id]
    assert [event.id for event in reconstruction.evidence_events] == [evidence.id]
    assert [event.id for event in reconstruction.architecture_events] == [architecture.id]
    assert [event.id for event in reconstruction.governance_events] == [governance.id]
    assert [event.id for event in reconstruction.outcome_events] == [outcome.id]


def test_reconstruct_decision_requires_decision(kernel: FOSKernel):
    thread = kernel.create_thread("t")
    note = kernel.append_event(thread.id, EventType.NOTE, {"text": "n"})
    with pytest.raises(ValueError, match="not a decision"):
        kernel.reconstruct_decision(note.id)


def test_reconstruct_missing_decision_fails(kernel: FOSKernel):
    with pytest.raises(ValueError, match="decision event not found"):
        kernel.reconstruct_decision("event:nope")


def test_file_store_round_trips_threads_and_events(tmp_path):
    store = FileStore(tmp_path / "fos")
    kernel = FOSKernel(store)
    thread = kernel.create_thread("persisted")
    event = kernel.append_event(thread.id, EventType.NOTE, {"text": "hello"})
    reopened = FOSKernel(FileStore(tmp_path / "fos"))
    assert reopened.get_thread(thread.id) == thread
    assert reopened.get_event(event.id) == event


def test_file_store_appends_jsonl(tmp_path):
    kernel = FOSKernel(FileStore(tmp_path / "fos"))
    thread = kernel.create_thread("persisted")
    kernel.append_event(thread.id, EventType.NOTE, {"text": "hello"})
    assert (tmp_path / "fos" / "threads.jsonl").exists()
    assert (tmp_path / "fos" / "events.jsonl").exists()


def test_project_cab_ledger_creates_thread():
    ledger = CABLedger()
    ledger.append(
        IntentRecord(
            intent_id="cab.intent.fos",
            authors=["steward"],
            articulated_at="2026-06-19T00:00:00Z",
            scope={"system": "FOS"},
            problem_statement="project CAB",
            desired_outcomes=["FOS continuity"],
            created_at="2026-06-19T00:00:00Z",
        )
    )
    thread = FOSKernel().project_cab_ledger(ledger)
    assert thread.label == "CAB projection"


def test_project_cab_ledger_maps_decision_to_decision_event():
    ledger = CABLedger()
    ledger.append(
        DecisionRecord(
            decision_id="cab.decision.fos",
            decision_makers=["steward"],
            chosen_option="FOS",
            rationale="needed",
            intent_refs=[],
            created_at="2026-06-19T00:00:00Z",
        )
    )
    kernel = FOSKernel()
    thread = kernel.project_cab_ledger(ledger)
    events = kernel.list_events_for_thread(thread.id)
    assert events[0].event_type == EventType.DECISION


def test_project_cab_ledger_maps_evidence_chain_to_evidence_event():
    ledger = CABLedger()
    ledger.append(
        EvidenceChain(
            chain_id="cab.evidence.fos",
            sources=["source"],
            methods=["test"],
            integrity_assessment="valid",
            created_at="2026-06-19T00:00:00Z",
        )
    )
    kernel = FOSKernel()
    thread = kernel.project_cab_ledger(ledger)
    assert kernel.list_events_for_thread(thread.id)[0].event_type == EventType.EVIDENCE


def test_project_cab_ledger_preserves_cab_payload():
    ledger = CABLedger()
    ledger.append(
        IntentRecord(
            intent_id="cab.intent.payload",
            authors=["steward"],
            articulated_at="2026-06-19T00:00:00Z",
            scope={"system": "FOS"},
            problem_statement="preserve",
            desired_outcomes=["payload"],
            created_at="2026-06-19T00:00:00Z",
        )
    )
    kernel = FOSKernel()
    thread = kernel.project_cab_ledger(ledger)
    event = kernel.list_events_for_thread(thread.id)[0]
    assert event.payload["cab_object_id"] == "cab.intent.payload"
    assert event.payload["problem_statement"] == "preserve"


def test_project_cab_ledger_links_cab_parent_refs():
    ledger = CABLedger()
    ledger.append(
        IntentRecord(
            intent_id="cab.intent.parent",
            authors=["steward"],
            articulated_at="2026-06-19T00:00:00Z",
            scope={"system": "FOS"},
            problem_statement="parent",
            desired_outcomes=["parent"],
            created_at="2026-06-19T00:00:00Z",
        )
    )
    ledger.append(
        DecisionRecord(
            decision_id="cab.decision.child",
            decision_makers=["steward"],
            chosen_option="child",
            rationale="because",
            intent_refs=["cab.intent.parent"],
            created_at="2026-06-19T00:01:00Z",
        )
    )
    kernel = FOSKernel()
    thread = kernel.project_cab_ledger(ledger)
    events = kernel.list_events_for_thread(thread.id)
    assert events[1].lineage == [events[0].id]


def test_projected_cab_decision_can_be_reconstructed():
    ledger = CABLedger()
    ledger.append(
        IntentRecord(
            intent_id="cab.intent.reconstruct",
            authors=["steward"],
            articulated_at="2026-06-19T00:00:00Z",
            scope={"system": "FOS"},
            problem_statement="reconstruct",
            desired_outcomes=["decision"],
            created_at="2026-06-19T00:00:00Z",
        )
    )
    ledger.append(
        DecisionRecord(
            decision_id="cab.decision.reconstruct",
            decision_makers=["steward"],
            chosen_option="FOS",
            rationale="because",
            intent_refs=["cab.intent.reconstruct"],
            created_at="2026-06-19T00:01:00Z",
        )
    )
    kernel = FOSKernel()
    thread = kernel.project_cab_ledger(ledger)
    decision = [event for event in kernel.list_events_for_thread(thread.id) if event.event_type == EventType.DECISION][0]
    reconstruction = kernel.reconstruct_decision(decision.id)
    assert reconstruction.discussion_events[0].payload["cab_object_id"] == "cab.intent.reconstruct"


def test_contract_document_exists():
    assert __import__("pathlib").Path("docs/contracts/FOS_V0_1_ARCHITECTURE.md").exists()
