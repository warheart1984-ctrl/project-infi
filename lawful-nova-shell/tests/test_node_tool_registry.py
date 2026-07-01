from __future__ import annotations

import json


def test_coder_tool_returns_updated_code_diff_and_receipt(monkeypatch) -> None:
    from nova.node.tools import coder_tool

    captured = {}

    def fake_generate(prompt, **kwargs):
        captured["prompt"] = prompt
        captured.update(kwargs)
        return "def health():\n    return 'ok'\n"

    monkeypatch.setattr(coder_tool, "generate", fake_generate)

    result = coder_tool.run(
        {
            "intent": "code",
            "file_path": "src/app.py",
            "instruction": "Add health endpoint",
            "current_code": "def old():\n    return 'old'\n",
            "context": "FastAPI route file",
            "temperature": 0.05,
        }
    )

    assert result["updated_code"] == "def health():\n    return 'ok'\n"
    assert result["file_path"] == "src/app.py"
    assert "--- src/app.py (original)" in result["diff"]
    assert "+++ src/app.py (updated)" in result["diff"]
    assert "-def old():" in result["diff"]
    assert "+def health():" in result["diff"]
    assert "Ring-2" in captured["prompt"]
    assert "FastAPI route file" in captured["prompt"]
    assert captured["temperature"] == 0.05
    assert captured["max_tokens"] == 4096
    assert result["receipts"] == ["coder_tool", "governance.patch_generated"]
    assert result["metadata"]["hunks"] == 1
    assert result["metadata"]["char_delta"] == len(result["updated_code"]) - len("def old():\n    return 'old'\n")


def test_coder_tool_strips_markdown_fences_and_counts_noop_hunks(monkeypatch) -> None:
    from nova.node.tools import coder_tool

    monkeypatch.setattr(
        coder_tool,
        "generate",
        lambda prompt, **kwargs: "```python\ndef old():\n    return 'old'\n```",
    )

    result = coder_tool.run(
        {
            "intent": "code",
            "file_path": "src/app.py",
            "instruction": "Keep code stable",
            "current_code": "def old():\n    return 'old'\n",
        }
    )

    assert result["updated_code"] == "def old():\n    return 'old'"
    assert result["metadata"]["hunks"] == 0


def test_wiring_tool_returns_glue_code_and_receipt(monkeypatch) -> None:
    from nova.node.tools import wiring_tool

    monkeypatch.setattr(wiring_tool, "generate", lambda prompt, **kwargs: "app.include_router(router)\n")

    result = wiring_tool.run(
        {
            "intent": "wire",
            "goal": "Connect coder_tool to /node/tool",
            "components": ["nova/api.py", "nova/node/tools/coder_tool.py"],
            "context": "FastAPI backend, governed node",
        }
    )

    assert result["glue_code"] == "app.include_router(router)\n"
    assert result["goal"] == "Connect coder_tool to /node/tool"
    assert result["components"] == ["nova/api.py", "nova/node/tools/coder_tool.py"]
    assert result["receipts"] == ["wiring_tool"]


def test_tool_registry_invokes_ring2_tools(monkeypatch) -> None:
    from nova.node.tools import registry

    monkeypatch.setattr(registry, "coder_run", lambda task: {"updated_code": task["current_code"], "receipts": ["coder_tool"]})

    result = registry.invoke_tool("code", {"intent": "code", "current_code": "print('x')"})

    assert result["receipts"] == ["coder_tool"]
    assert registry.TOOLS["code"]["profile"] == "N2"
    assert "patch" in registry.TOOLS["code"]["capabilities"]
    assert "wire" in registry.TOOLS
    assert "explain" in registry.TOOLS


def test_explain_tool_returns_structured_analysis(monkeypatch) -> None:
    from nova.node.tools import explain_tool

    captured = {}

    def fake_generate(prompt, **kwargs):
        captured["prompt"] = prompt
        captured.update(kwargs)
        return json.dumps(
            {
                "summary": "Adds health endpoint.",
                "risks": ["route collision"],
                "testing_recommendations": ["call /v1/health"],
                "why_this_approach": "Smallest route-only change.",
                "potential_breakage": "None expected.",
            }
        )

    monkeypatch.setattr(explain_tool, "generate", fake_generate)

    result = explain_tool.run(
        {
            "intent": "explain",
            "file_path": "src/app.py",
            "instruction": "Add health endpoint",
            "patch": "+@app.get('/v1/health')",
            "code_before": "",
            "code_after": "@app.get('/v1/health')\ndef health(): return {'status': 'ok'}",
        }
    )

    assert "constitutional analysis tool" in captured["prompt"]
    assert captured["temperature"] == 0.2
    assert result["analysis"]["summary"] == "Adds health endpoint."
    assert result["analysis"]["risks"] == ["route collision"]
    assert result["receipts"] == ["explain_tool", "governance.patch_explained"]
    assert result["metadata"]["analyzed_file"] == "src/app.py"


def test_local_model_falls_back_from_ollama_to_vllm(monkeypatch) -> None:
    from nova.node.tools import local_model

    calls = []

    def fake_post_json(url, payload, timeout):
        calls.append((url, payload, timeout))
        if url.endswith("/api/generate"):
            raise OSError("ollama offline")
        return {"choices": [{"text": "from vllm"}]}

    monkeypatch.setenv("NOVA_NODE_OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
    monkeypatch.setenv("NOVA_NODE_VLLM_URL", "http://127.0.0.1:8000/v1/completions")
    monkeypatch.setattr(local_model, "_post_json", fake_post_json)

    result = local_model.generate("hello", model="phi3", temperature=0.1, max_tokens=128)

    assert result == "from vllm"
    assert calls[0][0] == "http://127.0.0.1:11434/api/generate"
    assert calls[0][1] == {
        "model": "phi3",
        "prompt": "hello",
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 128},
    }
    assert calls[1][0] == "http://127.0.0.1:8000/v1/completions"
    assert calls[1][1] == {
        "model": "phi3",
        "prompt": "hello",
        "temperature": 0.1,
        "max_tokens": 128,
    }


def test_local_model_uses_non_streaming_ollama_json(monkeypatch) -> None:
    from nova.node.tools import local_model

    captured = {}

    def fake_post_json(url, payload, timeout):
        captured["url"] = url
        captured["payload"] = payload
        captured["timeout"] = timeout
        return {"response": "updated code"}

    monkeypatch.setenv("NOVA_NODE_OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
    monkeypatch.setattr(local_model, "_post_json", fake_post_json)

    result = local_model.generate("rewrite", temperature=0.15, max_tokens=256)

    assert result == "updated code"
    assert captured["url"] == "http://127.0.0.1:11434/api/generate"
    assert captured["payload"] == {
        "model": "qwen2.5-coder:3b",
        "prompt": "rewrite",
        "stream": False,
        "options": {"temperature": 0.15, "num_predict": 256},
    }


def test_coding_receipts_are_replayable(tmp_path, monkeypatch) -> None:
    from nova.node.tools.receipts import write_coding_receipt
    from nova.node.tools import replay_coding

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setattr(replay_coding, "generate", lambda prompt, **kwargs: "# hello\nprint('hello')\n")

    trace_file = write_coding_receipt(
        trace_id="trace-code-1",
        task={
            "intent": "code",
            "file_path": "src/app.py",
            "instruction": "Add a comment",
            "current_code": "print('hello')\n",
        },
        governance={"decision": "allowed", "policy_version": "1.0", "receipts": ["continuity"]},
        result={
            "updated_code": "# hello\nprint('hello')\n",
            "diff": "--- src/app.py (original)\n+++ src/app.py (updated)\n",
            "receipts": ["coder_tool"],
        },
        tool="code",
    )

    assert trace_file == "tool-receipts\\trace-code-1.json" or trace_file == "tool-receipts/trace-code-1.json"
    replayed = replay_coding.replay_coding("trace-code-1")

    assert replayed["trace_id"] == "trace-code-1"
    assert replayed["intent"] == "code"
    assert replayed["policy_version"] == "1.0"
    assert replayed["deterministic"] is True
    assert "diff_against_original" in replayed


def test_coding_tools_conformance_profile_documents_n2_slice() -> None:
    from pathlib import Path

    profile = Path(__file__).resolve().parents[1] / "nova" / "node" / "tools" / "conformance_coding.yaml"
    text = profile.read_text(encoding="utf-8")

    assert 'profile: "N2-coding-tools"' in text
    assert 'id: "CT-1"' in text
    assert 'id: "CT-2"' in text
    assert "Local-only inference" in text
    assert 'id: "CT-5"' in text


def test_node_tool_endpoint_governs_invokes_and_receipts(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient
    import nova.api as nova_api
    from nova.node.tools import coder_tool

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setenv("NOVA_NODE_ID", "node-tool-001")
    monkeypatch.setenv("NOVA_OPERATOR_KEY_ID", "operator-tool-key")
    monkeypatch.setattr(coder_tool, "generate", lambda prompt, **kwargs: "def health():\n    return 'ok'\n")

    client = TestClient(nova_api.app)
    response = client.post(
        "/node/tool",
        json={
            "task_id": "task-code-001",
            "intent": "code",
            "caller_id": "cursor",
            "file_path": "src/app.py",
            "instruction": "Add health endpoint",
            "current_code": "def old():\n    return 'old'\n",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["governance"]["decision"] == "allowed"
    assert payload["result"]["updated_code"] == "def health():\n    return 'ok'\n"
    assert payload["trace_file"].endswith(".json")

    trace_entry = json.loads((tmp_path / payload["trace_file"]).read_text(encoding="utf-8"))
    assert trace_entry["intent"] == "code"
    assert trace_entry["tool"] == "code"
    assert trace_entry["decision"] == "allowed"
    assert trace_entry["receipts"][-2:] == ["coder_tool", "governance.patch_generated"]
    assert "diff" in trace_entry

    continuity_log = tmp_path / "continuity.jsonl"
    entries = [json.loads(line) for line in continuity_log.read_text(encoding="utf-8").splitlines()]
    tool_receipts = [entry for entry in entries if entry.get("entry_type") == "nodeToolReceipt"]
    assert len(tool_receipts) == 1
    assert tool_receipts[0]["trace_id"] == payload["governance"]["trace_id"]

    event_log = tmp_path / "event-bus.jsonl"
    event_entries = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines()]
    channels = [entry["channel"] for entry in event_entries]
    assert "tool.invoked" in channels
    assert "tool.completed" in channels
    assert "governance.receipt_verified" in channels
    completed = next(entry for entry in event_entries if entry["channel"] == "tool.completed")
    assert completed["payload"]["tool_name"] == "code"
    assert completed["payload"]["trace_id"] == payload["governance"]["trace_id"]


def test_node_tool_endpoint_blocks_unknown_intent(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient
    import nova.api as nova_api

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))

    client = TestClient(nova_api.app)
    response = client.post("/node/tool", json={"intent": "orchestrate", "caller_id": "cursor"})

    assert response.status_code == 400
    assert response.json()["error"]["reason"] == "unknown-tool-intent"


def test_node_tools_endpoint_exposes_stateless_registry(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient
    import nova.api as nova_api

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))

    client = TestClient(nova_api.app)
    payload = client.get("/node/tools").json()

    names = [tool["name"] for tool in payload["tools"]]
    assert "code" in names
    assert "wire" in names
    code_tool = next(tool for tool in payload["tools"] if tool["name"] == "code")
    assert code_tool["profile"] == "N2"
    assert code_tool["stateless"] is True
    assert "patch" in code_tool["capabilities"]
