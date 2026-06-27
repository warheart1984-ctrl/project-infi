from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


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


def test_openai_models_lists_nova_local_for_cursor() -> None:
    from fastapi.testclient import TestClient
    from nova.api import app

    client = TestClient(app)
    response = client.get("/v1/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "list"
    assert any(model["id"] == "nova-local" for model in payload["data"])


def test_openai_chat_completions_wraps_lawful_nova_turn() -> None:
    from fastapi.testclient import TestClient
    from nova.api import app

    client = TestClient(app)
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "nova-local",
            "messages": [
                {"role": "system", "content": "You are Nova inside Cursor."},
                {"role": "user", "content": "observe cursor adapter"},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "chat.completion"
    assert payload["model"] == "nova-local"
    assert payload["choices"][0]["message"]["role"] == "assistant"
    assert "Nova Cortex" in payload["choices"][0]["message"]["content"]
    assert payload["nova"]["decision"] == "EXECUTED"
    assert payload["nova"]["receipt_verified"] is True


def test_openai_chat_completions_streams_sse_chunks() -> None:
    from fastapi.testclient import TestClient
    from nova.api import app

    client = TestClient(app)
    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={
            "model": "nova-local",
            "stream": True,
            "messages": [{"role": "user", "content": "observe streaming cursor adapter"}],
        },
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert '"object":"chat.completion.chunk"' in body
    assert "data: [DONE]" in body


def test_openai_compat_routes_require_api_key_when_configured(monkeypatch) -> None:
    from fastapi.testclient import TestClient
    from nova.api import app

    monkeypatch.setenv("NOVA_API_KEY", "cursor-secret")
    client = TestClient(app)

    models_response = client.get("/v1/models")
    chat_response = client.post(
        "/v1/chat/completions",
        json={"model": "nova-local", "messages": [{"role": "user", "content": "observe auth"}]},
    )

    assert models_response.status_code == 401
    assert chat_response.status_code == 401


def test_openai_compat_routes_accept_cursor_bearer_key(monkeypatch) -> None:
    from fastapi.testclient import TestClient
    from nova.api import app

    monkeypatch.setenv("NOVA_API_KEY", "cursor-secret")
    client = TestClient(app)
    headers = {"Authorization": "Bearer cursor-secret"}

    models_response = client.get("/v1/models", headers=headers)
    chat_response = client.post(
        "/v1/chat/completions",
        headers=headers,
        json={"model": "nova-local", "messages": [{"role": "user", "content": "observe auth"}]},
    )

    assert models_response.status_code == 200
    assert chat_response.status_code == 200
    assert chat_response.json()["nova"]["decision"] == "EXECUTED"


def test_openai_chat_completions_can_route_through_ollama_provider(monkeypatch) -> None:
    from fastapi.testclient import TestClient
    import nova.api as nova_api

    class FakeOllamaProvider:
        provider_id = "ollama"

        def __init__(self, *, base_url: str, model: str) -> None:
            self.base_url = base_url
            self.model = model

        async def invoke(self, messages, *, model, max_tokens, temperature):
            assert self.base_url == "http://127.0.0.1:11434"
            assert model == "qwen2.5-coder:7b"
            assert messages[-1]["role"] == "user"
            return SimpleNamespace(
                content="ollama-coded-response",
                provider="ollama",
                model=model,
                input_tokens=12,
                output_tokens=3,
            )

    monkeypatch.setenv("NOVA_PROVIDER", "ollama")
    monkeypatch.setenv("NOVA_OLLAMA_MODEL", "qwen2.5-coder:7b")
    monkeypatch.setattr(nova_api, "OllamaChatProvider", FakeOllamaProvider)

    client = TestClient(nova_api.app)
    response = client.post(
        "/v1/chat/completions",
        json={"model": "nova-local", "messages": [{"role": "user", "content": "write code"}]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["choices"][0]["message"]["content"] == "ollama-coded-response"
    receipt_payload = json.loads(payload["nova"]["receipt"]["payload"])
    assert receipt_payload["provider"] == "ollama"
    assert receipt_payload["model"] == "qwen2.5-coder:7b"
    assert receipt_payload["reproducibility"]["deterministic_core"] is False


def test_parent_stack_launchers_prefer_lawful_nova_package() -> None:
    repo_root = ROOT.parent
    windows_launcher = (repo_root / "scripts" / "start-nova-stack.ps1").read_text(encoding="utf-8")
    bash_launcher = (repo_root / "scripts" / "start-nova-stack.sh").read_text(encoding="utf-8")
    bash_common = (repo_root / "lawful-nova-shell" / "setup" / "lib" / "common.sh").read_text(encoding="utf-8")

    assert 'Join-Path $Root "lawful-nova-shell"' in windows_launcher
    assert '$ShellRoot;$Root' in windows_launcher
    assert '-WorkingDirectory $ShellRoot' in windows_launcher
    assert 'export PYTHONPATH="${shell_root}:${repo}${PYTHONPATH:+:${PYTHONPATH}}"' in bash_common
    assert '(cd "${shell_root}" && "${PY}" -m nova.api' in bash_launcher


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
