"""Spec scaffolds for domain runtimes not yet wired (relationship, cognitive, founder, opportunity, reputation).

Live runtimes: ``personal_continuity_runtime``, ``burnout_runtime``.
"""

from constitutional.runtime.domain_scaffolds.cognitive import RUNTIME_NAME as COGNITIVE_RUNTIME
from constitutional.runtime.domain_scaffolds.founder import RUNTIME_NAME as FOUNDER_RUNTIME
from constitutional.runtime.domain_scaffolds.opportunity import RUNTIME_NAME as OPPORTUNITY_RUNTIME
from constitutional.runtime.domain_scaffolds.relationship import RUNTIME_NAME as RELATIONSHIP_RUNTIME
from constitutional.runtime.domain_scaffolds.reputation import RUNTIME_NAME as REPUTATION_RUNTIME

__all__ = [
    "COGNITIVE_RUNTIME",
    "FOUNDER_RUNTIME",
    "OPPORTUNITY_RUNTIME",
    "RELATIONSHIP_RUNTIME",
    "REPUTATION_RUNTIME",
]
