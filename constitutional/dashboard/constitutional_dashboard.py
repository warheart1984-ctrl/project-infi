"""Full constitutional dashboard — survivability, fitness, purpose, hiddenness, threats."""

from __future__ import annotations

import sys
from typing import IO

from constitutional.hiddenness.hiddenness_panel import format_hiddenness_panel
from constitutional.hiddenness.hiddenness_runtime_v2 import load_hiddenness_state_v2
from constitutional.hiddenness.hiddenness_work_queue import (
    format_hiddenness_work_queue_panel,
    load_hiddenness_work_queue,
)
from constitutional.environment.panel import format_decision_environment_panel
from constitutional.significance.decision_environment_runtime import (
    DecisionEnvironmentRuntime,
    load_decision_environment_state,
)
from constitutional.priors.ledger import load_prior_ledger
from constitutional.priors.panel import format_prior_continuity_panel
from constitutional.priors.drift_detector import PriorDriftDetector, StewardPriorMap, load_prior_drift_state
from constitutional.salience.continuity_runtime import SalienceContinuityRuntime, load_salience_continuity_state
from constitutional.salience.ledger import load_salience_ledger
from constitutional.salience.panel import format_salience_panel
from constitutional.salience.perceptual_drift import PerceptualDriftDetector, load_perceptual_drift_state
from constitutional.jpss.invariant_drift_dashboard import (
    InvariantDriftDashboardRuntime,
    format_invariant_drift_panel,
    load_invariant_drift_dashboard,
)
from constitutional.legitimacy.legitimacy_drift import detect_legitimacy_drift, load_legitimacy_drift_state
from constitutional.legitimacy.legitimacy_exam import load_legitimacy_exam_result, run_legitimacy_exam
from constitutional.legitimacy.legitimacy_panel import format_legitimacy_panel
from constitutional.legitimacy.legitimacy_register import load_legitimacy_register
from constitutional.runtime.mission_fidelity_runtime import load_mission_fidelity_state
from constitutional.runtime.reconstructability_dashboard import load_reconstructability_dashboard
from constitutional.runtime.runtime import ConstitutionalStateRuntime


def format_constitutional_dashboard(csr: ConstitutionalStateRuntime) -> str:
    """Render the five-band constitutional dashboard as text."""
    dashboard = load_reconstructability_dashboard(csr)
    hiddenness = load_hiddenness_state_v2(csr)
    mission = load_mission_fidelity_state(csr)

    lines: list[str] = [
        "",
        "=== CONSTITUTIONAL DASHBOARD ===",
        f"Snapshot: {dashboard.snapshot_at.isoformat()}  v{dashboard.version}",
        "--------------------------------",
        f"System Survivability:      {dashboard.system_survivability_score:0.2f}",
        f"Steward Independence:      {dashboard.steward_independence_score:0.2f}",
        f"Founder Dependency Index:  {dashboard.founder_dependency_index:0.2f}",
        "",
        f"Reconstructability Fitness:{dashboard.reconstructability_fitness_score:0.2f}",
        f"Constitutional Debt:       {dashboard.constitutional_debt_score:0.2f}",
        f"Reconstructability Risk:   {dashboard.constitutional_risk_score:0.2f}",
        f"Personal Capacity:       {dashboard.personal_capacity_continuity:0.2f}",
        "",
        f"Purpose Fidelity:          {mission.purpose_fidelity_score:0.2f}",
        f"Mission Legibility:        {mission.mission_legibility_score:0.2f}",
        f"Purpose Continuity Index:  {mission.purpose_continuity_index:0.2f}",
    ]

    panel = format_hiddenness_panel(hiddenness).strip()
    if panel:
        lines.append("")
        lines.append(panel)

    queue = load_hiddenness_work_queue(csr)
    work_queue_panel = format_hiddenness_work_queue_panel(queue).strip()
    if work_queue_panel:
        lines.append("")
        lines.append(work_queue_panel)

    salience_ledger = load_salience_ledger(csr)
    salience_cont = load_salience_continuity_state(csr)
    if salience_cont is None:
        salience_cont = SalienceContinuityRuntime(csr, salience_ledger=salience_ledger).run()
    perceptual_drift = load_perceptual_drift_state(csr)
    if perceptual_drift is None:
        perceptual_drift = PerceptualDriftDetector(csr, salience_ledger=salience_ledger).run()
    salience_panel_text = format_salience_panel(
        salience_ledger,
        salience_cont,
        perceptual_drift,
    ).strip()
    if salience_panel_text:
        lines.append("")
        lines.append(salience_panel_text)

    prior_ledger = load_prior_ledger(csr)
    prior_drift = load_prior_drift_state(csr)
    if prior_drift is None:
        prior_drift = PriorDriftDetector(csr, prior_ledger=prior_ledger).run()
    prior_panel_text = format_prior_continuity_panel(
        prior_ledger,
        prior_drift,
        StewardPriorMap(),
    ).strip()
    if prior_panel_text:
        lines.append("")
        lines.append(prior_panel_text)

    try:
        env_state = load_decision_environment_state(csr)
    except KeyError:
        env_state = DecisionEnvironmentRuntime(csr).run()
    env_panel_text = format_decision_environment_panel(env_state).strip()
    if env_panel_text:
        lines.append("")
        lines.append(env_panel_text)

    invariant_dashboard = load_invariant_drift_dashboard(csr)
    if invariant_dashboard is None:
        invariant_dashboard = InvariantDriftDashboardRuntime(csr).update_snapshot()
    invariant_panel = format_invariant_drift_panel(invariant_dashboard).strip()
    if invariant_panel:
        lines.append("")
        lines.append(invariant_panel)

    legitimacy_register = load_legitimacy_register(csr)
    legitimacy_exam = load_legitimacy_exam_result(csr)
    if legitimacy_exam is None and legitimacy_register.active_stewards():
        legitimacy_exam = run_legitimacy_exam(csr, legitimacy_register.active_stewards()[0].steward_id)
    legitimacy_drift = load_legitimacy_drift_state(csr) or detect_legitimacy_drift(csr)
    legitimacy_panel = format_legitimacy_panel(
        register=legitimacy_register,
        exam=legitimacy_exam,
        drift=legitimacy_drift,
    ).strip()
    if legitimacy_panel:
        lines.append("")
        lines.append(legitimacy_panel)

    lines.extend(
        [
            "R-F Threats:",
            f"  {[t.value for t in dashboard.failed_surfaces or dashboard.active_threats]}",
            "P-F Threats:",
            f"  {[t.value for t in mission.failed_surfaces]}",
            "H-F Threats:",
            f"  {[t.value for t in hiddenness.failed_surfaces]}",
            "================================",
            "",
        ]
    )
    return "\n".join(lines)


def render_constitutional_dashboard(
    csr: ConstitutionalStateRuntime,
    *,
    stream: IO[str] | None = None,
) -> str:
    """Print (or write) the full constitutional dashboard."""
    text = format_constitutional_dashboard(csr)
    out = stream if stream is not None else sys.stdout
    out.write(text)
    if stream is None:
        out.flush()
    return text


# Alias matching steward-facing spec naming.
render_dashboard = render_constitutional_dashboard
format_dashboard = format_constitutional_dashboard
