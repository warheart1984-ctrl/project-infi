"""Backward-compatible import path — use ``constitutional.runtime`` in new code."""

from constitutional.runtime import *  # noqa: F403
from constitutional.runtime import __all__ as __all__
