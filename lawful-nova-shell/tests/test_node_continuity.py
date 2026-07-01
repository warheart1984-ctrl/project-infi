from __future__ import annotations


def test_continuity_log_is_append_only(tmp_path, monkeypatch) -> None:
    from nova.node.continuity import append_event, read_events

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))

    e1 = append_event("submit", {"task_id": "t-1"})
    e2 = append_event("result", {"task_id": "t-1"})
    events = read_events()

    assert e1 in events
    assert e2 in events
    assert events[0]["kind"] == "submit"
    assert events[1]["kind"] == "result"
