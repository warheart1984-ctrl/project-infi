"""AAIS constitutional substrate — Meta Lawbook spine and ingress membranes."""

from src.substrate.meta_law_engine import (
    ConstitutionalLawbookError,
    bootstrap_constitutional_lawbook,
    resolve_constitutional_context,
)

__all__ = [
    "ConstitutionalLawbookError",
    "bootstrap_constitutional_lawbook",
    "resolve_constitutional_context",
]
