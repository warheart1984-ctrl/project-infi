from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

import pytest


SOVEREIGN_IDE_ROOT = Path(__file__).resolve().parents[2] / "sovereign-ide"
if str(SOVEREIGN_IDE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOVEREIGN_IDE_ROOT))

from runtime import (  # type: ignore[import-not-found]
    CodexLoader,
    FederationBootstrapper,
    SovereignIdeApiServer,
)
from sovereign_ide.app import main as sovereign_main  # type: ignore[import-not-found]


def test_codex_loader_reads_directory_payloads(tmp_path: Path) -> None:
    source = tmp_path / "sovereign"
    source.mkdir()
    (source / "constitution_hardware.json").write_text('{"guard":"enabled"}', encoding="utf-8")
    (source / "spec_goa_cpu.json").write_text('{"name":"goa"}', encoding="utf-8")
    (source / "conf_goa_cpu.json").write_text('{"status":"green"}', encoding="utf-8")

    loader = CodexLoader(base=source)
    payload = loader.load_all()

    assert payload["constitution"] == {"guard": "enabled"}
    assert payload["specs"]["goa_cpu"] == {"name": "goa"}
    assert payload["conformance"]["goa_cpu"] == {"status": "green"}


def test_codex_loader_reads_single_ledger_file(tmp_path: Path) -> None:
    ledger_file = tmp_path / "ledger.json"
    ledger_file.write_text(
        json.dumps(
            {
                "constitution": {"guard": "enabled"},
                "specs": {"timeline": {"route": "GET /api/timeline?epoch=<int>"}},
                "conformance": {"timeline": {"status": "ok"}},
            }
        ),
        encoding="utf-8",
    )

    loader = CodexLoader(base=ledger_file)
    payload = loader.load_all()

    assert payload["constitution"] == {"guard": "enabled"}
    assert payload["specs"]["timeline"]["route"] == "GET /api/timeline?epoch=<int>"
    assert payload["conformance"]["timeline"]["status"] == "ok"


def test_api_server_serves_guided_routes(tmp_path: Path) -> None:
    source = tmp_path / "sovereign"
    source.mkdir()
    (source / "constitution_hardware.json").write_text('{"guard":"enabled"}', encoding="utf-8")
    (source / "spec_goa_cpu.json").write_text('{"name":"goa"}', encoding="utf-8")
    (source / "conf_goa_cpu.json").write_text('{"status":"green"}', encoding="utf-8")

    loader = CodexLoader(base=source)
    loader.load_all()
    federation = FederationBootstrapper(loader)
    federation.bootstrap()

    from runtime.state import SovereignRuntimeContext  # type: ignore[import-not-found]

    ctx = SovereignRuntimeContext(codex=loader, federation=federation)
    server = SovereignIdeApiServer(ctx, host="127.0.0.1", port=0)
    server.start()
    try:
        timeline = _get_json(f"{server.base_url}/api/timeline?epoch=17")
        shader = _post_json(f"{server.base_url}/api/shader/update", {"resonance": 0.9, "pulse_frequency": 2.5})
        organism = _get_json(f"{server.base_url}/api/organism/state")
        consensus = _get_json(f"{server.base_url}/api/consensus/votes")
        ledger = _get_json(f"{server.base_url}/api/ledger/blocks")
        pulse = _post_json(f"{server.base_url}/api/audio/pulse", {"waveform": "triangle"})
        health = _get_json(f"{server.base_url}/health")

        assert timeline["epoch"] == 17
        assert timeline["replay_mode"] == "governed"
        assert shader["accepted"] is True
        assert shader["parameters"]["pulse_frequency"] == 2.5
        assert organism["telemetry"]["status"] == "online"
        assert consensus["votes"]["favor"] == 14
        assert ledger["immutable"] is True
        assert pulse["soundscape"]["waveform"] == "triangle"
        assert health["app_name"] == "Sovereign IDE"
        assert health["surfaces"]
    finally:
        server.close()


def test_bootstrap_only_reports_summary(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ledger_file = tmp_path / "ledger.json"
    ledger_file.write_text(
        json.dumps(
            {
                "constitution": {"guard": "enabled"},
                "specs": {"timeline": {"route": "GET /api/timeline?epoch=<int>"}},
                "conformance": {"timeline": {"status": "ok"}},
            }
        ),
        encoding="utf-8",
    )

    exit_code = sovereign_main(["--bootstrap-only", "--ledger-path", str(ledger_file)])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "sovereign-ide bootstrap complete" in captured
    assert "surfaces=6" in captured


def _get_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(url: str, body: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))
