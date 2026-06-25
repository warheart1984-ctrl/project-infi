"""Shared runtime services for workflow shell and Celery workers."""

from __future__ import annotations

from pathlib import Path

from app.config import DATA_DIR
from src.agent_fault_journal import AgentFaultJournal
from src.project_infi_law import ProjectInfiLaw
from src.run_ledger import RunLedger

RUNTIME_DIR = (DATA_DIR / "runtime").resolve()
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

run_ledger = RunLedger(runtime_dir=RUNTIME_DIR)
project_infi_law = ProjectInfiLaw(run_ledger=run_ledger)
agent_fault_journal = AgentFaultJournal(path=RUNTIME_DIR / "agent-faults.ndjson")
