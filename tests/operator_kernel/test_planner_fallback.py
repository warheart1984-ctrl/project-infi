"""Tests for planner fallback merge when LLM returns non-write tool_calls."""

from __future__ import annotations

from operator_kernel.lawful_brain.planner_fallback import enrich_parsed_plan


def test_enrich_injects_write_patch_when_llm_returned_list_files_only():
    parsed = {
        "tool_calls": [
            {"id": "llm-1", "name": "list_files", "args": {"path": "."}},
        ],
        "steps": ["list workspace"],
    }
    out = enrich_parsed_plan(
        parsed,
        "Modify hello.py to print Hello Jon",
        read_only=False,
    )
    names = [c["name"] for c in out["tool_calls"]]
    assert names[0] == "write_patch"
    assert "list_files" in names
    assert out["tool_calls"][0]["args"]["path"] == "hello.py"


def test_follow_up_session_transcript_prefers_modify_over_create(tmp_path):
    (tmp_path / "hello.py").write_text('print("Hello World")\n', encoding="utf-8")
    session_intent = (
        "Continue this agent session.\n\n"
        "user: Create a new file hello.py that prints Hello World\n"
        "assistant: Completed step 1 with 1 tool call(s).\n"
        "user: Modify hello.py to print Hello Jon"
    )
    parsed = {"tool_calls": [], "steps": []}
    out = enrich_parsed_plan(
        parsed,
        session_intent,
        read_only=False,
        workspace_root=tmp_path,
    )
    assert out["tool_calls"][0]["name"] == "write_patch"
    assert out["tool_calls"][0]["args"]["path"] == "hello.py"
    assert "Hello Jon" in out["tool_calls"][0]["args"]["diff"]


def test_enrich_analyze_replaces_single_list_files_with_full_explore_plan():
    parsed = {
        "tool_calls": [
            {"id": "llm-1", "name": "list_files", "args": {"path": "."}},
        ],
    }
    out = enrich_parsed_plan(
        parsed,
        "Analyze the entire workspace tree in detail",
        read_only=False,
    )
    list_calls = [c for c in out["tool_calls"] if c["name"] == "list_files"]
    assert len(list_calls) >= 5


def test_enrich_overrides_llm_create_patch_on_modify_intent(tmp_path):
    (tmp_path / "hello.py").write_text('print("Hello World")\n', encoding="utf-8")
    parsed = {
        "tool_calls": [
            {
                "id": "w1",
                "name": "write_patch",
                "args": {
                    "path": "hello.py",
                    "diff": "--- /dev/null\n+++ b/hello.py\n@@ -0,0 +1,1 @@\n+print('Hello World')\n",
                },
            },
        ],
    }
    out = enrich_parsed_plan(
        parsed,
        "Modify hello.py to print Hello Jon",
        read_only=False,
        workspace_root=tmp_path,
    )
    assert out["tool_calls"][0]["name"] == "write_patch"
    assert "Hello Jon" in out["tool_calls"][0]["args"]["diff"]
    assert "--- /dev/null" not in out["tool_calls"][0]["args"]["diff"]
