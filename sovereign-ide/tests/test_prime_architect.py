from __future__ import annotations

from pathlib import Path

from plugins.prime_architect import PrimeArchitectPlugin
from runtime.codex_loader import CodexLoader
from runtime.prime_architect import (
    HarmonicEngine,
    LineageLogger,
    MandalaVisualizer,
    PrimeArchitectRuntime,
    ReplayVerifier,
)
from runtime import build_prime_architect_action_payload, build_prime_architect_payload
from sovereign_ide.app import build_runtime

try:
    from PyQt6.QtWidgets import QApplication
except Exception:  # pragma: no cover
    QApplication = None


class DummyIDE:
    def __init__(self) -> None:
        self.commands: dict[str, object] = {}

    def register_command(self, name, handler):
        self.commands[name] = handler


def test_codex_loader_loads_prime_architect_manifest() -> None:
    loader = CodexLoader()
    bundle = loader.load_all()

    assert loader.base == (Path(__file__).resolve().parents[1] / "sovereign").resolve()
    assert bundle["constitution"]["app_name"] == "Sovereign IDE"
    assert bundle["specs"]["prime_architect"]["name"] == "PrimeArchitect"
    assert bundle["conformance"]["goa_cpu"]["conforms"] is True


def test_harmonic_engine_and_visualizer_render_deterministically() -> None:
    engine = HarmonicEngine()
    visualizer = MandalaVisualizer()

    assert engine.get_resonance("continuity") == 1.618
    assert engine.pulse_frequency("replay") == 27.18

    svg = visualizer.render({"invariant": "continuity", "intensity": 0.5})

    assert 'data-invariant="continuity"' in svg
    assert 'stroke="#00ffff"' in svg
    assert 'fill="#0088ff"' in svg


def test_lineage_logger_and_replay_verifier_round_trip() -> None:
    logger = LineageLogger()
    replay = ReplayVerifier()

    event = logger.record("promotion.approve_selected", None, "token-1")
    trace = logger.trace(event["chain_id"])
    report = replay.validate(
        trace,
        {
            "command": "promotion.approve_selected",
            "selected": ("selected",),
            "replay_token": "token-1",
        },
    )

    assert trace == [event]
    assert report["matches"] is False
    audit = replay.audit(trace)
    assert audit["event_count"] == 1
    assert audit["command_ids"] == ["promotion.approve_selected"]


def test_prime_architect_runtime_produces_command_outputs() -> None:
    runtime = PrimeArchitectRuntime()

    approval = runtime.approve_selected()
    trace = runtime.trace_lineage()
    replay = runtime.verify_replay()

    assert approval["status"] in {"approved", "review"}
    assert approval["selected"] == ("selected",)
    assert approval["trace"] == trace
    assert replay["event_count"] == 1


def test_plugin_registers_prime_architect_commands() -> None:
    ide = DummyIDE()
    plugin = PrimeArchitectPlugin(ide)
    plugin.activate()

    assert "sovereign.start" in ide.commands
    assert "promotion.approve_selected" in ide.commands
    assert "lineage.trace" in ide.commands
    assert "replay.verify" in ide.commands
    assert plugin.ctx.architect is plugin.runtime


def test_build_runtime_exposes_architect_summary() -> None:
    runtime = build_runtime()
    summary = runtime["ctx"].summary_lines()

    assert any(line.startswith("architect.loaded=True") for line in summary)
    assert any(line.startswith("architect.commands=3") for line in summary)


def test_prime_architect_api_payloads_expose_actions() -> None:
    runtime = build_runtime()
    ctx = runtime["ctx"]

    manifest = build_prime_architect_payload(ctx)
    approval = build_prime_architect_action_payload(ctx, "approve_selected", {"selected": "alpha"})
    chain_id = approval["result"]["event"]["chain_id"]
    trace = build_prime_architect_action_payload(ctx, "trace", {"chain_id": chain_id})
    replay = build_prime_architect_action_payload(ctx, "replay", {"chain_id": chain_id})

    assert manifest["architect"]["loaded"] is True
    assert len(manifest["architect"]["commands"]) == 3
    assert approval["accepted"] is True
    assert approval["result"]["selected"] == ("alpha",)
    assert trace["accepted"] is True
    assert isinstance(trace["result"], list)
    assert replay["accepted"] is True
    assert replay["result"]["event_count"] >= 1


def test_prime_architect_panel_updates_inline_report() -> None:
    if QApplication is None:
        return

    from PyQt6.QtWidgets import QLabel

    from sovereign_ide.widgets import PrimeArchitectPanel

    app = QApplication.instance() or QApplication([])
    runtime = build_runtime()
    architect = runtime["ctx"].architect
    architect.lineage.record("alpha.chain", None, "token-a")
    architect.lineage.record("beta.chain", None, "token-b")
    panel = PrimeArchitectPanel(runtime["ctx"])

    assert panel._chain_list.count() >= 1
    panel._chain_list.setCurrentRow(0)
    first_item = panel._chain_list.item(0)
    assert first_item is not None
    first_row = panel._chain_list.itemWidget(first_item)
    assert first_row is not None
    assert first_row.property("active") is True
    chip_texts = [label.text().lower() for label in first_row.findChildren(QLabel)]
    assert any("latest" in text or "approved" in text or "stale" in text for text in chip_texts)
    badge = first_row.findChild(QLabel, "primeChainCountBadge")
    assert badge is not None
    assert badge.text() == "1"
    replay_pill = first_row.findChild(QLabel, "primeChainReplayPill")
    assert replay_pill is not None
    assert replay_pill.text().startswith("replay ")
    assert replay_pill.property("status") in {"ok", "review", "stale"}
    panel.verify_replay()
    latest_report = panel._report.toPlainText()
    assert "Replay report [alpha.chain]" in latest_report
    assert "event_count" in latest_report
