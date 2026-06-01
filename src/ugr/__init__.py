"""Unified Governed Runtime (UGR) — lazy exports to avoid import cycles and stdlib shadowing."""

from __future__ import annotations

from typing import Any

__all__ = [
    "ConvergenceEngine",
    "LaneManager",
    "PatternLedgerStore",
    "UnifiedPatternLedger",
    "normalize_cogos_pattern_record",
    "UnifiedGovernedRuntime",
    "DistributedUnifiedGovernedRuntime",
    "GovernedIngestionPipeline",
    "IngestionConfig",
    "build_ugr_runtime",
    "ugr_runtime",
    "UGRMeshClients",
    "load_mesh_config",
    "converge_lane_results",
    "run_lanes",
]


def __getattr__(name: str) -> Any:
    if name == "ConvergenceEngine":
        from src.ugr.convergence_engine import ConvergenceEngine

        return ConvergenceEngine
    if name == "converge_lane_results":
        from src.ugr.convergence_engine import converge_lane_results

        return converge_lane_results
    if name == "LaneManager":
        from src.ugr.lane_manager import LaneManager

        return LaneManager
    if name == "run_lanes":
        from src.ugr.lane_manager import run_lanes

        return run_lanes
    if name == "PatternLedgerStore":
        from src.ugr.pattern_ledger import PatternLedgerStore

        return PatternLedgerStore
    if name == "UnifiedPatternLedger":
        from src.ugr.unified_pattern_ledger import UnifiedPatternLedger

        return UnifiedPatternLedger
    if name == "normalize_cogos_pattern_record":
        from src.ugr.unified_pattern_ledger import normalize_cogos_pattern_record

        return normalize_cogos_pattern_record
    if name in ("UnifiedGovernedRuntime", "build_ugr_runtime", "ugr_runtime"):
        from src.ugr import unified_runtime as _ur

        return getattr(_ur, name)
    if name in ("DistributedUnifiedGovernedRuntime", "UGRMeshClients", "load_mesh_config"):
        from src.ugr import cloud as _cloud

        return getattr(_cloud, name)
    if name in ("GovernedIngestionPipeline", "IngestionConfig"):
        from src.ugr import ingestion as _ing

        return getattr(_ing, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
