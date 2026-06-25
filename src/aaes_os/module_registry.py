"""Re-export ModuleRegistry from the modules package (legacy import path)."""

from __future__ import annotations

from src.aaes_os.modules.daniel import (
    DanielExecutionModule,
    DanielModule,
    ModuleRegistry,
)
from src.aaes_os.modules.nexus import NexusExecutionModule

__all__ = ["DanielExecutionModule", "DanielModule", "ModuleRegistry", "NexusExecutionModule"]
