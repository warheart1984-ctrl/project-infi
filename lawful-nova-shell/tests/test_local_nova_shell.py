from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_local_nova_cli_health() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "nova.cli", "health", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["service"] == "nova_local_cli"
    assert payload["direct_lawful_llm"]["status"] == "ok"


def test_local_nova_api_chat_exposes_chain_contract() -> None:
    from fastapi.testclient import TestClient
    from nova.api import app

    client = TestClient(app)
    response = client.post(
        "/v1/chat",
        json={"prompt": "observe lawful nova", "tenant_id": "local", "capability": "observe"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "EXECUTED"
    assert payload["receipt_verified"] is True
    assert payload["chain"]["identity"]["instance_id"]
    assert payload["chain"]["trace"]["trace_id"]
    assert payload["chain"]["authority_boundary"]["operator_authority"] == "external"
    assert payload["chain"]["reproducibility"]["prompt_sha256"]


def test_local_nova_api_openai_chat_completions_contract() -> None:
    from fastapi.testclient import TestClient
    from nova.api import app

    client = TestClient(app)
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "lawful-nova",
            "messages": [
                {"role": "system", "content": "You are Nova."},
                {"role": "user", "content": "observe lawful nova"},
            ],
            "temperature": 0,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "chat.completion"
    assert payload["model"] == "lawful-nova"
    assert payload["choices"][0]["message"]["role"] == "assistant"
    assert isinstance(payload["choices"][0]["message"]["content"], str)
    assert payload["choices"][0]["finish_reason"] == "stop"
    assert payload["usage"]["total_tokens"] >= 2
    assert "lawful_nova" not in payload
    assert response.headers.get("x-lawful-nova-receipt")


def test_local_nova_api_openai_responses_format_contract() -> None:
    from fastapi.testclient import TestClient
    from nova.api import app

    client = TestClient(app)
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "lawful-nova",
            "input": [
                {"role": "user", "content": "observe lawful nova via responses payload"},
            ],
            "temperature": 0,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "response"
    assert payload["output"][0]["content"][0]["text"]


def test_local_nova_api_openai_responses_endpoint_alias() -> None:
    from fastapi.testclient import TestClient
    from nova.api import app

    client = TestClient(app)
    response = client.post(
        "/v1/responses",
        json={
            "model": "lawful-nova",
            "input": "ping",
        },
    )
    assert response.status_code == 200
    assert response.json()["object"] == "response"


def test_local_nova_api_openai_models_contract() -> None:
    from fastapi.testclient import TestClient
    from nova.api import app

    client = TestClient(app)
    response = client.get("/v1/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "list"
    model_ids = {item["id"] for item in payload["data"]}
    assert "lawful-nova" in model_ids
    assert "nvidia/nemotron-3-ultra-550b-a55b" in model_ids


def test_openai_cursor_compat_normalizes_tools() -> None:
    from nova.openai_cursor_compat import normalize_request

    normalized = normalize_request(
        {
            "model": "lawful-nova",
            "messages": [{"role": "user", "content": "hi"}],
            "tools": [
                {
                    "name": "read_file",
                    "description": "Read a file",
                    "parameters": {"type": "object", "properties": {}},
                }
            ],
        }
    )
    assert normalized.tools
    assert normalized.tools[0]["type"] == "function"
    assert normalized.tools[0]["function"]["name"] == "read_file"


def test_productization_gate_checks_chain_contract() -> None:
    out = ROOT / ".runtime" / "test_nova_productization_report.json"
    result = subprocess.run(
        [sys.executable, "scripts/nova_productization_gate.py", "--json-out", str(out)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["local_lawful_slice_ready"] is True
    assert payload["checks"]["chain_contract"]["status"] == "ok"
