"""CLI tests for continuity command."""

from __future__ import annotations

from continuity_sdk.cli import main


def test_cli_info() -> None:
    assert main(["info"]) == 0


def test_cli_demo_falling_object(capsys) -> None:
    assert main(["demo", "falling-object"]) == 0
    out = capsys.readouterr().out
    assert "Running MVCD" in out
    assert "Contradiction detected" in out
    assert "Calibration delta:" in out


def test_cli_mission_005(capsys) -> None:
    assert main(["mission", "005"]) == 0
    out = capsys.readouterr().out
    assert "3 stewards" in out
    assert "Status: PASSED" in out


def test_cli_console(capsys) -> None:
    assert main(["console"]) == 0
    out = capsys.readouterr().out
    assert "CONTINUITY STEWARD CONSOLE" in out
    assert "K‑∞ compliance" in out or "K-∞ compliance" in out


def test_steward_console_render() -> None:
    from continuity_sdk import render_steward_console

    text = render_steward_console()
    assert "CE‑1 CORRECTION ENGINE" in text or "CE-1 CORRECTION ENGINE" in text
    assert "CLG‑1 LINEAGE TREE" in text or "CLG-1 LINEAGE TREE" in text


def test_entry_point_registered() -> None:
    from importlib.metadata import entry_points

    scripts = {ep.name: ep.value for ep in entry_points(group="console_scripts")}
    assert "continuity" in scripts
    assert scripts["continuity"] == "continuity_sdk.cli:main"
