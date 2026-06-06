"""Compatibility entrypoint for Jarvis launcher tests and scripts."""

# Mythic: Jarvis Launcher
# Engineering: JarvisLauncherCompat
from __future__ import annotations

import sys

from src.entrypoints import start_jarvis as _start_jarvis

sys.modules[__name__] = _start_jarvis
