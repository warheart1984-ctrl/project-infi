"""CSS-1 — Full Continuity Stack Specification (final form, nine layers)."""

from src.continuity.css.spec import (
    CONTINUITY_HEART,
    CSS1_LAYERS,
    CSS1_MODULES,
    CSS1_REFERENCE,
    CSS1_VERSION,
    FULL_CONTINUITY_REQUIREMENTS,
    PHASE_3_5_LABEL,
    PHASE_4_LABEL,
    UNIFIED_CONTINUITY_CONDITION,
)
from src.continuity.css.ligp import LIGPAssessment, assess_ligp, format_ligp_invariants
from src.continuity.css.sec import (
    GovernanceEvent,
    SEC1Assessment,
    assess_sec1,
    assess_sed1,
    extract_governance_events,
)
from src.continuity.css.fap import (
    FAP1Assessment,
    FounderInsight,
    FounderResponse,
    SuccessorInsight,
    assess_fap1,
)
from src.continuity.css.fcrm import FCRM1Assessment, assess_fcrm1
from src.continuity.css.ssde import SSDE1Assessment, assess_ssde1, assess_ssde1_from_ce_log
from src.continuity.css.cer import CER1CycleResult, ingest_lineage_event, run_cer_cycle
from src.continuity.css.orchestrator import CSS1Assessment, assess_css1, resolve_stack_phase
from src.continuity.css.adm1 import ADM1Assessment, assess_adm1
from src.continuity.css.k4 import K4Assessment, assess_k4

# Resolve forward refs after submodules are fully loaded (avoids import cycle via cos1).
CER1CycleResult.model_rebuild(
    _types_namespace={
        "ADM1Assessment": ADM1Assessment,
        "K4Assessment": K4Assessment,
    }
)
CSS1Assessment.model_rebuild(
    _types_namespace={
        "ADM1Assessment": ADM1Assessment,
        "K4Assessment": K4Assessment,
    }
)

__all__ = [
    "ADM1Assessment",
    "CONTINUITY_HEART",
    "CSS1Assessment",
    "CSS1_LAYERS",
    "CSS1_MODULES",
    "CSS1_REFERENCE",
    "CSS1_VERSION",
    "CER1CycleResult",
    "FAP1Assessment",
    "FCRM1Assessment",
    "FULL_CONTINUITY_REQUIREMENTS",
    "FounderInsight",
    "FounderResponse",
    "GovernanceEvent",
    "K4Assessment",
    "LIGPAssessment",
    "PHASE_3_5_LABEL",
    "PHASE_4_LABEL",
    "SEC1Assessment",
    "SSDE1Assessment",
    "SuccessorInsight",
    "UNIFIED_CONTINUITY_CONDITION",
    "assess_adm1",
    "assess_css1",
    "assess_fap1",
    "assess_fcrm1",
    "assess_k4",
    "assess_ligp",
    "assess_sec1",
    "assess_sed1",
    "assess_ssde1",
    "assess_ssde1_from_ce_log",
    "extract_governance_events",
    "format_ligp_invariants",
    "ingest_lineage_event",
    "resolve_stack_phase",
    "run_cer_cycle",
]
