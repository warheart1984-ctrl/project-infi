from __future__ import annotations

import json


def test_provider_registry_builds_local_ollama_and_external() -> None:
    from nova.providers import build_provider
    from nova.providers.provider_external import ExternalProvider
    from nova.providers.provider_local import LocalDeterministicProvider
    from nova.providers.provider_ollama import OllamaProvider

    assert isinstance(build_provider({}), LocalDeterministicProvider)

    ollama = build_provider({
        "provider": "ollama",
        "ollama_url": "http://fake-ollama",
        "ollama_model": "qwen2.5-coder:7b",
    })
    assert isinstance(ollama, OllamaProvider)
    assert ollama.base_url == "http://fake-ollama"
    assert ollama.model == "qwen2.5-coder:7b"

    external = build_provider({
        "provider": "external",
        "external_url": "https://api.example.test/v1",
        "external_model": "gpt-test",
        "external_api_key": "secret",
    })
    assert isinstance(external, ExternalProvider)


def test_ollama_provider_returns_completion_and_receipt(monkeypatch) -> None:
    from nova.providers.provider_ollama import OllamaProvider

    captured = {}

    def fake_post_json(url, payload, *, timeout, headers=None):
        captured.update({"url": url, "payload": payload, "timeout": timeout, "headers": headers})
        return {
            "model": "qwen2.5-coder:7b",
            "message": {"content": "Hello from Ollama"},
            "prompt_eval_count": 4,
            "eval_count": 3,
        }

    monkeypatch.setattr("nova.providers.provider_ollama.post_json", fake_post_json)
    provider = OllamaProvider(base_url="http://fake-ollama", model="qwen2.5-coder:7b", timeout=11)
    governed_request = {
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 16,
        "temperature": 0,
        "slice_id": "test-slice",
        "slice_version": "1.0",
        "continuity_hash": "abc123",
        "governance_path": ["rsl.validate"],
    }

    result = provider.chat_completion(governed_request)

    assert captured["url"] == "http://fake-ollama/api/chat"
    assert captured["payload"]["stream"] is False
    assert captured["payload"]["options"]["num_predict"] == 16
    completion = result["completion"]
    assert completion["id"].startswith("ollama-")
    assert completion["object"] == "chat.completion"
    assert completion["model"] == "qwen2.5-coder:7b"
    assert completion["choices"][0]["message"]["role"] == "assistant"
    assert completion["choices"][0]["message"]["content"] == "Hello from Ollama"
    receipt = result["receipt"]
    assert receipt["provider"] == "ollama"
    assert receipt["model"] == "qwen2.5-coder:7b"
    assert receipt["governed_request"] == governed_request
    assert receipt["normalized_completion"] == completion
    assert receipt["deterministic_core"] is False
    assert receipt["rsl_version"] == "1.0"
    assert receipt["slice_id"] == "test-slice"
    assert receipt["continuity_hash"] == "abc123"
    assert receipt["evidence_chain"]


def test_ollama_streaming_provider_emits_cursor_chunks(monkeypatch) -> None:
    from nova.providers.provider_ollama import OllamaProvider

    lines = [
        json.dumps({"message": {"content": "hel"}, "done": False}).encode("utf-8"),
        json.dumps({"message": {"content": "lo"}, "done": True}).encode("utf-8"),
    ]

    monkeypatch.setattr(
        "nova.providers.provider_ollama.post_json_lines",
        lambda url, payload, *, timeout: iter(lines),
    )
    provider = OllamaProvider(base_url="http://fake-ollama", model="qwen2.5-coder:7b")

    chunks = list(provider.chat_completion_stream({"messages": [{"role": "user", "content": "hi"}]}))

    assert chunks[0]["object"] == "chat.completion.chunk"
    assert chunks[0]["choices"][0]["delta"]["role"] == "assistant"
    assert chunks[0]["choices"][0]["delta"]["content"] == "hel"
    assert chunks[1]["choices"][0]["delta"]["content"] == "lo"
    assert chunks[-1]["completion"]["object"] == "chat.completion"
    assert chunks[-1]["completion"]["choices"][0]["message"]["content"] == "hello"
    assert chunks[-1]["receipt"]["provider"] == "ollama"


def test_api_models_health_completions_metrics_and_streaming(monkeypatch) -> None:
    from fastapi.testclient import TestClient
    import nova.api as nova_api

    class FakeProvider:
        provider_id = "ollama"
        model = "qwen2.5-coder:7b"

        def chat_completion(self, governed_request):
            text = governed_request["messages"][-1]["content"]
            return {
                "completion": {
                    "id": "fake-completion-1",
                    "object": "chat.completion",
                    "created": 123,
                    "model": self.model,
                    "choices": [
                        {
                            "index": 0,
                            "finish_reason": "stop",
                            "message": {"role": "assistant", "content": f"echo:{text}"},
                        }
                    ],
                },
                "receipt": {"provider": "ollama"},
            }

        def chat_completion_stream(self, governed_request):
            yield {
                "id": "stream-1",
                "object": "chat.completion.chunk",
                "created": 123,
                "model": self.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": "part"},
                        "finish_reason": None,
                    }
                ],
            }
            yield {"completion": self.chat_completion(governed_request)["completion"], "receipt": {"provider": "ollama"}}

    monkeypatch.setenv("NOVA_PROVIDER", "ollama")
    monkeypatch.setenv("NOVA_OLLAMA_MODEL", "qwen2.5-coder:7b")
    monkeypatch.setattr(nova_api, "build_provider", lambda config: FakeProvider())
    nova_api.app.state.nova_config = nova_api.load_nova_config()
    client = TestClient(nova_api.app)

    health = client.get("/health").json()
    assert health["status"] == "ok"
    assert health["provider"] == "ollama"
    assert health["model"] == "qwen2.5-coder:7b"

    models = client.get("/v1/models").json()
    assert models["object"] == "list"
    assert {m["id"] for m in models["data"]} == {"nova-local", "qwen2.5-coder:7b"}

    completion = client.post("/v1/completions", json={"model": "nova-local", "prompt": "plain prompt"}).json()
    assert completion["object"] == "text_completion"
    assert completion["choices"][0]["text"] == "echo:plain prompt"

    chat = client.post(
        "/v1/chat/completions",
        json={"model": "qwen2.5-coder:7b", "messages": [{"role": "user", "content": "chat prompt"}]},
    ).json()
    assert chat["object"] == "chat.completion"
    assert chat["choices"][0]["message"]["content"] == "echo:chat prompt"

    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={"model": "qwen2.5-coder:7b", "stream": True, "messages": [{"role": "user", "content": "stream"}]},
    ) as response:
        body = "".join(response.iter_text())
    assert response.status_code == 200
    assert '"object":"chat.completion.chunk"' in body
    assert '"completion"' in body
    assert "data: [DONE]" in body

    metrics = client.get("/metrics").json()
    assert metrics["requests"] >= 3
    assert metrics["stream_requests"] >= 1
    assert metrics["provider"] == "ollama"
    assert metrics["model"] == "qwen2.5-coder:7b"
