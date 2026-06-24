# src/continuity_sdk/lawful_llm_adapter.py

from src.crk1.lawful_llm_adapter import FallingObjectModel
from src.crk1.lawful_llm_adapter import LawfulLLMAdapter as _CoreAdapter


class LawfulLLMAdapter(_CoreAdapter):
    """
    Public SDK facade for the constitutional LLM adapter.

    Re-exports the core adapter with a stable, minimal surface.
    """

    pass


__all__ = ["LawfulLLMAdapter", "FallingObjectModel"]
