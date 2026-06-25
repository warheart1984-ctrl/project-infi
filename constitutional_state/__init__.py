"""Backward-compatible import path — use ``constitutional.core`` in new code."""

from constitutional.core import *  # noqa: F403
from constitutional.core import __all__ as __all__
