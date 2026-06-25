"""Backward-compatible import path — use ``constitutional.runtime.governance_gate`` in new code."""

from constitutional.runtime.governance_gate import *  # noqa: F403
from constitutional.runtime.governance_gate import _BOOT_COMPLETED  # noqa: F401
