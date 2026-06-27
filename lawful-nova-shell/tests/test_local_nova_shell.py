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
