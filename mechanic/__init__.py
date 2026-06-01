"""AI Mechanic — governed AI workflow scan, diagnosis, and dry-run rebuild."""

from mechanic.genome.extractor import extract_process_genome
from mechanic.diagnosis.engine import diagnose_genome

__all__ = ["extract_process_genome", "diagnose_genome"]
