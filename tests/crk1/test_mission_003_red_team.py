"""Mission #003 — Red-Team Protocol (M3-B)."""

from __future__ import annotations

from src.crk1.external_reproduction_harness import prepare_continuity_substrate
from src.crk1.red_team_protocol import RedTeamProtocol


def test_red_team_protocol_passes(runtime) -> None:
    report = RedTeamProtocol(runtime).run_all()
    assert report.passed, report.summary()
    assert not report.failures


def test_red_team_class_a_mechanical(runtime) -> None:
    identity = runtime.kernel.ledgers.identity.id
    attacks = RedTeamProtocol(runtime).run_class_a_mechanical(identity)
    assert attacks
    assert all(attack.status == "PASS" for attack in attacks)


def test_red_team_class_b_structural(runtime) -> None:
    prepare_continuity_substrate(runtime)
    identity = runtime.kernel.ledgers.identity.id
    attacks = RedTeamProtocol(runtime).run_class_b_structural(identity)
    assert all(attack.status in ("REJECTED", "PASS") for attack in attacks)


def test_red_team_class_c_semantic(runtime) -> None:
    prepare_continuity_substrate(runtime)
    attacks = RedTeamProtocol(runtime).run_class_c_semantic()
    assert all(attack.status in ("REJECTED", "PASS") for attack in attacks)
