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
    windows_path = repo_root / "scripts" / "start-nova-stack.ps1"
    bash_path = repo_root / "scripts" / "start-nova-stack.sh"
    if not windows_path.exists() or not bash_path.exists():
        windows_quickstart = (ROOT / "quickstart.ps1").read_text(encoding="utf-8")
        bash_quickstart = (ROOT / "quickstart.sh").read_text(encoding="utf-8")
        assert "python.exe -m nova.api" in windows_quickstart
        assert "python -m nova.api" in bash_quickstart
        assert "npm start" in windows_quickstart
        assert "npm start" in bash_quickstart
        return

    windows_launcher = windows_path.read_text(encoding="utf-8")
    bash_launcher = bash_path.read_text(encoding="utf-8")
    bash_common = (ROOT / "setup" / "lib" / "common.sh").read_text(encoding="utf-8")

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


def test_deepseek_coding_substrate_files_and_profiles_are_wired() -> None:
    windows_profile = (ROOT / "config" / "profile.ps1").read_text(encoding="utf-8")
    unix_profile = (ROOT / "setup" / "novrc.sh").read_text(encoding="utf-8")
    deepseek_ps1 = ROOT / "bin" / "nova-chat-deepseek.ps1"
    registry = ROOT / "config" / "nova-model-registry.json"
    modelfile = ROOT / "config" / "ollama" / "Modelfile.coding-substrate-1"

    assert deepseek_ps1.exists()
    assert "ollama run $Model $Prompt" in deepseek_ps1.read_text(encoding="utf-8")
    assert '$NovaModels = @{' in windows_profile
    assert '"codex" = "qwen2.5-coder:3b"' in windows_profile
    assert '"deepseek" = "deepseek-coder:6.7b"' in windows_profile
    assert '"qwen" = "qwen2.5-coder:3b"' in windows_profile
    assert '"qwen7" = "qwen2.5-coder:7b"' in windows_profile
    assert '"coding-substrate" = "coding-substrate-1:latest"' in windows_profile
    assert '"analysis" = "gemma4:latest"' in windows_profile
    assert "function global:Invoke-NovaCodexPrompt" in windows_profile
    assert "function global:Invoke-NovaModel" in windows_profile
    assert "function global:Invoke-NovaCodex" in windows_profile
    assert "function global:Invoke-NovaReplay" in windows_profile
    assert "function global:nova-codex" in windows_profile
    assert "function global:nova-deepseek" in windows_profile
    assert "function global:nova-qwen" in windows_profile
    assert "function global:nova-analysis" in windows_profile
    assert "$HOME\\nova-receipts.jsonl" in windows_profile
    assert "$HOME\\nova-substrates.json" in windows_profile
    assert "policyVersion = $Global:NovaPolicyVersion" in windows_profile
    assert "CODING-SUBSTRATE-1 inside the Nova lawful runtime" in windows_profile
    assert "Intent -> Plan -> Code -> Receipt" in windows_profile
    assert "ConvertTo-Json -Depth 8 -Compress" in windows_profile
    assert "[System.Security.Cryptography.SHA256]::Create()" in windows_profile
    assert "nova-deepseek" in unix_profile
    assert "coding-substrate-1:latest" in windows_profile
    assert "nova-chat  | nova-codex  | nova-deepseek  | nova-qwen  | nova-analysis" in windows_profile
    assert "novr       | novtest     | novdoc         | novstack" in windows_profile
    assert "nova-chat | novr | novtest | novpr | novdoc | novsec | novstack | nova-deepseek" in unix_profile

    registry_payload = json.loads(registry.read_text(encoding="utf-8"))
    assert registry_payload["coding_substrate"]["id"] == "coding-substrate-1"
    assert registry_payload["coding_substrate"]["model"] == "qwen2.5-coder:3b"
    assert registry_payload["coding_substrate"]["tier"] == 15
    assert registry_payload["deepseek_coder"]["model"] == "deepseek-coder:6.7b"
    assert registry_payload["qwen_coder_7b"]["model"] == "qwen2.5-coder:7b"
    assert registry_payload["coding_substrate_full"]["model"] == "coding-substrate-1:latest"
    assert registry_payload["gemma4"]["model"] == "gemma4:latest"

    modelfile_text = modelfile.read_text(encoding="utf-8")
    assert "FROM qwen2.5-coder:3b" in modelfile_text
    assert "PARAMETER temperature 0.15" in modelfile_text
    assert "PARAMETER top_p 0.9" in modelfile_text
    assert "PARAMETER num_ctx 8192" in modelfile_text
    assert 'PARAMETER stop "<END>"' in modelfile_text
    assert "CODING-SUBSTRATE-1" in modelfile_text
    assert "STRUCTURE FIRST" in modelfile_text
    assert "EVIDENCE & RECEIPTS" in modelfile_text
    assert "CODEx CONTINUATION MODE" in modelfile_text

    qwen_modelfile = ROOT / "config" / "ollama" / "Modelfile.qwen-governed-1"
    qwen_text = qwen_modelfile.read_text(encoding="utf-8")
    assert "FROM qwen2.5-coder:3b" in qwen_text
    assert "PARAMETER temperature 0.15" in qwen_text
    assert "PARAMETER top_p 0.9" in qwen_text
    assert "PARAMETER num_ctx 8192" in qwen_text
    assert "QWEN-GOVERNED-1 inside the Nova lawful runtime" in qwen_text
    assert "policyVersion CRK-1.0.0" in qwen_text


def test_configure_coding_substrate_writes_registry_and_codex_config(tmp_path) -> None:
    registry_out = tmp_path / "nova-model-registry.json"
    codex_out = tmp_path / "ollama-launch-models.json"
    substrates_out = tmp_path / "nova-substrates.json"
    capabilities_out = tmp_path / "nova-substrate-capabilities.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/configure_coding_substrate.py",
            "--registry-out",
            str(registry_out),
            "--codex-out",
            str(codex_out),
            "--substrates-out",
            str(substrates_out),
            "--capabilities-out",
            str(capabilities_out),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    registry_payload = json.loads(registry_out.read_text(encoding="utf-8"))
    codex_payload = json.loads(codex_out.read_text(encoding="utf-8"))
    substrates_payload = json.loads(substrates_out.read_text(encoding="utf-8"))
    capabilities_payload = json.loads(capabilities_out.read_text(encoding="utf-8"))
    assert registry_payload["coding_substrate"]["id"] == "coding-substrate-1"
    assert registry_payload["coding_substrate"]["model"] == "qwen2.5-coder:3b"
    assert registry_payload["deepseek_coder"]["model"] == "deepseek-coder:6.7b"
    assert registry_payload["qwen_coder_7b"]["model"] == "qwen2.5-coder:7b"
    assert registry_payload["coding_substrate_full"]["model"] == "coding-substrate-1:latest"
    assert registry_payload["gemma4"]["model"] == "gemma4:latest"
    assert codex_payload == {"default_model": "qwen2.5-coder:3b"}
    assert substrates_payload["coding_substrate_1"] == {
        "id": "coding-substrate-1",
        "backend": "ollama",
        "model": "qwen2.5-coder:3b",
        "role": "codegen",
        "tier": 15,
        "node": "nova-node-1",
    }
    assert substrates_payload["analysis_substrate_1"]["id"] == "analysis-1"
    assert substrates_payload["qwen_governed_1"] == {
        "id": "qwen-governed-1",
        "backend": "ollama",
        "model": "qwen2.5-coder:3b",
        "role": "codegen",
        "tier": 15,
        "node": "nova-node-1",
    }
    assert capabilities_payload["qwen-governed-1"]["capabilities"] == [
        "generate_code",
        "refactor_code",
        "explain_code",
        "write_tests",
    ]
    assert "no_external_network" in capabilities_payload["qwen-governed-1"]["constraints"]


def test_governance_module_federation_and_daemon_surfaces_are_wired() -> None:
    module = ROOT / "modules" / "NovaGovernance" / "NovaGovernance.psm1"
    federate = ROOT / "bin" / "nova-federate.ps1"
    daemon = ROOT / "governance-daemon" / "index.js"
    capabilities = ROOT / "config" / "nova-substrate-capabilities.json"

    module_text = module.read_text(encoding="utf-8")
    federate_text = federate.read_text(encoding="utf-8")
    daemon_text = daemon.read_text(encoding="utf-8")
    capabilities_payload = json.loads(capabilities.read_text(encoding="utf-8"))

    for text in (module_text, federate_text):
        assert "nova-node-1" in text
        assert "coding-substrate-1" in text
        assert "qwen-governed-1" in text
        assert "CRK-1.0.0" in text
        assert "policyVersion" in text
        assert "nodeId" in text
        assert "substrateId" in text
        assert "eventId" in text
        assert "parentId" in text
        assert "federation-merge" in text
        assert "drift-resolution" in text

    assert "function Invoke-NovaFederate" in module_text
    assert "function Resolve-Drift" in module_text
    assert "function Show-NovaContinuityGraph" in module_text
    assert "function nova-qwen" in module_text
    assert "Export-ModuleMember" in module_text

    assert "Invoke-NovaFederate" in federate_text
    assert "Write-FederationReceipt" in federate_text
    assert "substrates" in federate_text

    assert "createServer" in daemon_text
    assert '"/receipts"' in daemon_text
    assert '"/drift"' in daemon_text
    assert '"/substrates/qwen"' in daemon_text
    assert '"/substrates/qwen/receipts"' in daemon_text
    assert "qwen-governed-1" in daemon_text
    assert "substrates: [...new Set" in daemon_text
    assert "express" not in daemon_text.lower()

    assert capabilities_payload["coding-substrate-1"]["constraints"] == [
        "no_global_state",
        "no_unbounded_io",
        "no_external_network",
    ]
    assert capabilities_payload["qwen-governed-1"]["id"] == "qwen-governed-1"
