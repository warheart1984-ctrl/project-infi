"""UGR governed ingestion (Phase 3)."""

from src.ugr.ingestion.config import IngestionConfig, IngestionSource
from src.ugr.ingestion.pipeline import GovernedIngestionPipeline, IngestionRunResult

__all__ = [
    "GovernedIngestionPipeline",
    "IngestionConfig",
    "IngestionRunResult",
    "IngestionSource",
]
