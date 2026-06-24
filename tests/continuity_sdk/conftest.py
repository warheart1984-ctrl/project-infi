"""Register top-level `continuity_sdk` alias for editable and test imports."""

from __future__ import annotations

import sys

import src.continuity_sdk as _continuity_sdk

sys.modules.setdefault("continuity_sdk", _continuity_sdk)
