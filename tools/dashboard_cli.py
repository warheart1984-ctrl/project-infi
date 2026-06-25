#!/usr/bin/env python3
"""Terminal v0 survivability dashboard — Article S constitutional cockpit."""

from __future__ import annotations

import argparse
import sys

from constitutional.core.articles import ARTICLE_P_REFERENCE, ARTICLE_S_INVARIANT, PURPOSE_CONTINUITY_INVARIANT
from constitutional.runtime.reconstructability_dashboard_runtime import (
    ReconstructabilityDashboardRuntime,
    load_reconstructability_dashboard,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime

from operator_kernel.csr import CSR
from operator_kernel.succession_integration import build_article_s2_integration_snapshot


def render_survivability_dashboard(csr: ConstitutionalStateRuntime) -> None:
    snapshot = build_article_s2_integration_snapshot(csr, escalate_amendment=False)
    dashboard = snapshot.dashboard

    print("\n=== SURVIVABILITY DASHBOARD (Article S / S-2) ===")
    print(f"Snapshot: {dashboard.snapshot_at.isoformat()}  v{dashboard.version}")
    print(f"Article S-2: {snapshot.article_s2_reference}")
    print("-------------------------------------------")
    print()
    print(f"System Survivability Score:     {dashboard.system_survivability_score:0.2f}  [{snapshot.zones.get('system_survivability_score', '—')}]")
    print(f"Steward Independence Score:     {dashboard.steward_independence_score:0.2f}  [{snapshot.zones.get('steward_independence_score', '—')}]")
    print(f"Founder Dependency Index:       {dashboard.founder_dependency_index:0.2f}  [{snapshot.zones.get('founder_dependency_index', '—')}]")
    print()
    print(f"Reconstructability Fitness:     {dashboard.reconstructability_fitness_score:0.2f}  [{snapshot.zones.get('reconstructability_fitness_score', '—')}]")
    print(f"Succession Readiness Score:     {snapshot.article_s1.succession_readiness_score:0.2f}  [{snapshot.zones.get('succession_readiness_score', '—')}]")
    print(f"Constitutional Debt:            {dashboard.constitutional_debt_score:0.2f}")
    print(f"Reconstructability Risk:        {dashboard.constitutional_risk_score:0.2f}")
    print(f"Personal Capacity Continuity:   {dashboard.personal_capacity_continuity:0.2f}")
    print()
    print(f"Article S-1 compliant:          {snapshot.article_s1.compliant}")
    print(f"Governance gate:                {snapshot.governance.level} (allow={snapshot.governance.allow})")
    print(f"Succession ready (S-2):         {snapshot.succession.ready}")
    if snapshot.survivability_amendment:
        print(f"Open amendment:                 {snapshot.survivability_amendment.template_id}")
        print(f"Amendment triggers:             {', '.join(snapshot.survivability_amendment.triggers)}")
    print(f"Constitutional Debt:            {dashboard.constitutional_debt_score:0.2f}")
    print(f"Reconstructability Risk:        {dashboard.constitutional_risk_score:0.2f}")
    print(f"Personal Capacity Continuity:   {dashboard.personal_capacity_continuity:0.2f}")
    print()
    print("Active Threat Surfaces (R-F):")
    for threat in dashboard.active_threats:
        print(f" - {threat.value}")
    print()
    print("--- Purpose Continuity (Article P) ---")
    print(f"Purpose Continuity Index:     {dashboard.purpose_continuity_index:0.2f}")
    print(f"Purpose Fidelity:             {dashboard.purpose_fidelity_score:0.2f}")
    print(f"Mission Legibility:           {dashboard.mission_legibility_score:0.2f}")
    print(f"Invariant Interpretation:      {dashboard.invariant_interpretation_score:0.2f}")
    print()
    print("Purpose Threat Surfaces (P-F):")
    for threat in dashboard.purpose_threats:
        print(f" - {threat.value}")
    print()
    print(f"Implicit Assumptions Required:  {dashboard.implicit_assumptions_required}")
    print("-------------------------------------------")
    print(f"Article S: {ARTICLE_S_INVARIANT}")
    print(f"Governed:  {dashboard.article_reference}")
    print(f"Article P: {PURPOSE_CONTINUITY_INVARIANT}")
    print(f"Governed:  {dashboard.purpose_article_reference}")
    print("===========================================\n")


def render_dashboard_cli(csr: ConstitutionalStateRuntime) -> None:
    """Alias for backward compatibility."""
    render_survivability_dashboard(csr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render survivability dashboard (terminal v0)")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Recompute dashboard snapshot before rendering",
    )
    args = parser.parse_args(argv)

    csr = CSR
    if args.refresh:
        ReconstructabilityDashboardRuntime(csr).update_snapshot()
    render_survivability_dashboard(csr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
