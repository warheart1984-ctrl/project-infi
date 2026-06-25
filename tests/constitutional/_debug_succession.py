from datetime import UTC, datetime

from constitutional.hiddenness.hiddenness_runtime import HiddennessRuntime, load_hiddenness_state
from constitutional.runtime.domain_receipts_store import clear_domain_memory_index
from constitutional.runtime.mission_fidelity_interactive import submit_mission_fidelity_answers
from constitutional.runtime.mission_fidelity_runtime import MissionFidelityRuntime
from constitutional.runtime.reconstructability_dashboard import build_reconstructability_dashboard
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.salience.governance import (
    succession_perceptual_drift_ready,
    succession_salience_continuity_ready,
    succession_salience_judgment_ready,
)
from constitutional.salience.judgment_runtime import seed_passing_salience_judgment
from constitutional.priors.governance import succession_prior_continuity_ready
from constitutional.runtime.survivability_amendment import cold_start_steward_passes
from constitutional.significance.significance_governance import (
    succession_significance_continuity_ready,
    succession_significance_evolution_ready,
    succession_significance_judgment_ready,
)
from constitutional.significance.significance_judgment_runtime import seed_passing_significance_judgment
from operator_kernel.succession import succession_blocked, succession_ready
from tests.constitutional.test_hiddenness_runtime import (
    _all_answers,
    _seed_mission,
    _seed_salience_ledger_for_succession,
)

clear_domain_memory_index()
csr = ConstitutionalStateRuntime(persist_root="/tmp/succ_debug")
from constitutional.core.articles import PURPOSE_CONTINUITY_INVARIANT

csr.register_invariant(PURPOSE_CONTINUITY_INVARIANT, "Article P")
csr.register_invariant("CRITICAL_SYSTEMS_MUST_REMAIN_RECONSTRUCTABLE", "Article R")
_seed_mission(csr)
submit_mission_fidelity_answers(csr, _all_answers())
MissionFidelityRuntime(csr).run_test()
HiddennessRuntime(csr).run_audit()
seed_passing_significance_judgment(csr)
seed_passing_salience_judgment(csr)
_seed_salience_ledger_for_succession(csr)
now = datetime.now(UTC)
dashboard = build_reconstructability_dashboard(csr, snapshot_at=now, version=1)
dashboard = dashboard.model_copy(
    update={
        "steward_independence_score": 0.85,
        "system_survivability_score": 0.85,
        "founder_dependency_index": 0.15,
        "reconstructability_fitness_score": 0.85,
        "implicit_assumptions_required": 0,
        "active_threats": [],
    }
)
hiddenness = load_hiddenness_state(csr)
print("prior", succession_prior_continuity_ready(csr))
print("salience_j", succession_salience_judgment_ready(csr))
print("salience_c", succession_salience_continuity_ready(csr))
print("perceptual", succession_perceptual_drift_ready(csr))
print("sig_j", succession_significance_judgment_ready(csr))
print("sig_c", succession_significance_continuity_ready(csr))
print("sig_e", succession_significance_evolution_ready(csr))
print("cold_start", cold_start_steward_passes(dashboard, csr=csr))
blocked, reasons = succession_blocked(dashboard, csr=csr, hiddenness=hiddenness)
print("blocked", blocked, reasons)
print("ready", succession_ready(dashboard, interactive_passed=True, csr=csr, hiddenness=hiddenness))
