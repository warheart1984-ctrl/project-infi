"""Pluggable genome extraction adapters."""

from mechanic.genome.adapters.base import GenomeAdapter, list_adapters, run_adapters
from mechanic.genome.adapters.registry import get_adapter

__all__ = ["GenomeAdapter", "get_adapter", "list_adapters", "run_adapters"]
