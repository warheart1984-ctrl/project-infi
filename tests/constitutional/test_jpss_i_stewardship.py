"""Tests for JPSS-I stewardship handbook, adaptation playbook, and invariant dashboard."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from constitutional.eck2 import ECK2Runtime
from constitutional.jpss import (
    InvariantDriftZone,
    InvariantEntry,
    StewardshipMode,
    assess_stewardship_situation,
    classify_drift_zone,
    format_adaptation_playbook,
    format_invariant_drift_panel,
    format_stewardship_handbook,
    load_invariant_drift_dashboard,
    load_invariant_register,
)
from constitutional.jpss.invariant_drift_dashboard import InvariantDriftDashboardRuntime
from constitutional.jpss.invariant_register import save_invariant_register
from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.runtime.runtime import ConstitutionalStateRuntime


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    clear_domain_memory_index()


@pytest.fixture
def csr(tmp_path) -> ConstitutionalStateRuntime:
    from constitutional.core.articles import PURPOSE_CONTINUITY_INVARIANT

    runtime = ConstitutionalStateRuntime(persist_root=tmp_path)
    runtime.register_invariant(PURPOSE_CONTINUITY_INVARIANT, "Article P")
    runtime.register_invariant(
        "CRITICAL_SYSTEMS_MUST_REMAIN_RECONSTRUCTABLE",
        "Article R",
    )
    return runtime


def test_stewardship_handbook_renders_core_sections() -> None:
    text = format_stewardship_handbook()
    assert "WHAT STEWARDSHIP ACTUALLY IS" in text
    assert "THE TWO JUDGMENT LAYERS" in text
    assert "THE DUAL PIPELINES OF ECK-2" in text
    assert "THE STEWARD'S OATH" in text
    assert "preserve what must endure" in text


def test_adaptation_playbook_renders_matrix_and_modes() -> None:
    text = format_adaptation_playbook()
    assert "FOUR MODES OF STEWARDSHIP" in text
    assert "DECISION MATRIX" in text
    assert "Over-Adaptation" in text
    assert "Identity Re-Anchoring" in text


def test_assess_stewardship_situation_modes() -> None:
    assert assess_stewardship_situation(identity_unclear=True).mode == StewardshipMode.IDENTITY_RE_ANCHORING
    assert assess_stewardship_situation(identity_threatened=True).mode == StewardshipMode.INVARIANT_DEFENSE
    assert assess_stewardship_situation(environment_shift=True).mode == (
        StewardshipMode.IDENTITY_ALIGNED_ADAPTATION
    )
    assert assess_stewardship_situation().mode == StewardshipMode.ADAPTIVE_ACTION


def test_drift_zone_classification() -> None:
    assert classify_drift_zone(0.95) == InvariantDriftZone.GREEN
    assert classify_drift_zone(0.85) == InvariantDriftZone.YELLOW
    assert classify_drift_zone(0.70) == InvariantDriftZone.RED


def test_invariant_dashboard_green_zone(csr: ConstitutionalStateRuntime) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    register = load_invariant_register(csr)
    base = {
        "purpose_clauses": ["preserve constitutional continuity"],
        "core_values": ["non-derogable"],
        "commitments": ["succession gate required"],
        "identity_markers": ["eck-2 dual pipeline"],
        "sacred_constraints": ["never bypass succession gate"],
    }
    register.append(InvariantEntry(timestamp=now, steward_id="steward-a", **base))
    save_invariant_register(csr, register)

    dashboard = InvariantDriftDashboardRuntime(csr).update_snapshot(snapshot_at=now)
    assert dashboard.zone == InvariantDriftZone.GREEN
    assert dashboard.drift_index == 1.0
    assert not dashboard.requires_intervention
    assert len(dashboard.weekly_checklist) >= 7

    panel = format_invariant_drift_panel(dashboard)
    assert "Purpose Stability" in panel
    assert "Weekly steward checklist" in panel


def test_invariant_dashboard_red_zone_on_erosion(csr: ConstitutionalStateRuntime) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    register = load_invariant_register(csr)
    base = {
        "purpose_clauses": ["preserve constitutional continuity"],
        "core_values": ["non-derogable"],
        "commitments": ["succession gate required"],
        "identity_markers": ["eck-2 dual pipeline"],
        "sacred_constraints": ["never bypass succession gate"],
    }
    register.append(InvariantEntry(timestamp=now, steward_id="steward-a", **base))
    register.append(
        InvariantEntry(
            timestamp=now,
            steward_id="steward-b",
            purpose_clauses=[],
            core_values=["non-derogable"],
            commitments=["succession gate required"],
            identity_markers=[],
            sacred_constraints=[],
        )
    )
    save_invariant_register(csr, register)

    dashboard = InvariantDriftDashboardRuntime(csr).update_snapshot(snapshot_at=now)
    assert dashboard.zone == InvariantDriftZone.RED
    assert dashboard.requires_intervention
    assert dashboard.purpose.flagged_erosions


def test_invariant_dashboard_persists_and_loads(csr: ConstitutionalStateRuntime) -> None:
    from constitutional.jpss import canonical_passing_responses

    ECK2Runtime(csr).run(
        {
            "decision_id": "dash-dec-001",
            "available_signals": ["fitness"],
            "expected_signals": ["reconstructability"],
            "constraints_active": ["article_r"],
            "outcome": "observe",
            "rationale": "Dashboard persistence test.",
            "invariant_defaults": {
                "purpose_clauses": ["preserve continuity"],
                "core_values": ["non-derogable"],
                "commitments": ["gate required"],
                "identity_markers": ["eck-2"],
                "sacred_constraints": ["no bypass"],
            },
            "stewardship_responses": canonical_passing_responses(),
        }
    )
    dashboard = load_invariant_drift_dashboard(csr)
    assert dashboard is not None
    assert dashboard.drift_index >= 0.8
