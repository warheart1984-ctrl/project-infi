from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

from skillzmcgee.core.adapters.llm_adapter import build_llm_from_env
from skillzmcgee.core.workflow import Workflow
from skillzmcgee.governance.continuity_ledger import (
    FileContinuityLedger,
    SQLiteContinuityLedger,
    ValidatedLedger,
)
from skillzmcgee.governance.state_accumulator import StateAccumulator
from skillzmcgee.governance.validator import MinimalValidator
from skillzmcgee.slices.slice_custom import echo_slice

DEFAULT_LEDGER_PATH = Path(".runtime") / "skillzmcgee" / "receipts.jsonl"
DEFAULT_SQLITE_LEDGER_PATH = Path(".runtime") / "skillzmcgee" / "receipts.sqlite3"


def build_ledger(
    ledger_path: str | Path | None,
    validator: MinimalValidator,
    ledger_backend: str = "auto",
) -> ValidatedLedger:
    backend = ledger_backend.lower()
    if ledger_path is None:
        if backend in {"auto", "memory"}:
            return ValidatedLedger(validator)
        if backend == "sqlite":
            return SQLiteContinuityLedger(DEFAULT_SQLITE_LEDGER_PATH, validator)
        if backend == "jsonl":
            return FileContinuityLedger(DEFAULT_LEDGER_PATH, validator)
        raise ValueError(f"unsupported SkillzMcGee ledger backend: {ledger_backend}")

    path = Path(ledger_path)
    if backend == "auto":
        backend = "sqlite" if path.suffix.lower() in {".db", ".sqlite", ".sqlite3"} else "jsonl"
    if backend == "sqlite":
        return SQLiteContinuityLedger(path, validator)
    if backend == "jsonl":
        return FileContinuityLedger(path, validator)
    if backend == "memory":
        return ValidatedLedger(validator)
    raise ValueError(f"unsupported SkillzMcGee ledger backend: {ledger_backend}")


def boot(
    llm: Callable[[str], str] | None = None,
    actor: str = "skillz",
    ledger_path: str | Path | None = None,
    ledger_backend: str = "auto",
    llm_provider: str | None = None,
    llm_url: str | None = None,
    llm_endpoint: str | None = None,
) -> Workflow:
    """Boot the minimal governed runtime and return its workflow engine."""
    validator = MinimalValidator()
    ledger = build_ledger(ledger_path, validator, ledger_backend)
    accumulator = StateAccumulator()
    accumulator.rebuild_from_ledger(ledger)
    configured_llm = llm or build_llm_from_env(
        provider=llm_provider,
        base_url=llm_url,
        endpoint=llm_endpoint,
    )
    return Workflow(ledger=ledger, accumulator=accumulator, actor=actor, llm=configured_llm)


def main() -> None:
    parser = argparse.ArgumentParser(prog="skillzmcgee")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("run-demo", "history", "state", "ask"),
        default="run-demo",
    )
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument(
        "--ledger-backend",
        choices=("auto", "memory", "jsonl", "sqlite"),
        default="auto",
    )
    parser.add_argument("--prompt")
    parser.add_argument("--context-slice")
    parser.add_argument("--llm-provider")
    parser.add_argument("--llm-url")
    parser.add_argument("--llm-endpoint")
    args = parser.parse_args()

    workflow = boot(
        ledger_path=args.ledger,
        ledger_backend=args.ledger_backend,
        llm_provider=args.llm_provider,
        llm_url=args.llm_url,
        llm_endpoint=args.llm_endpoint,
    )

    if args.command == "history":
        print(json.dumps(workflow.ledger.all(), indent=2, sort_keys=True))
        return

    if args.command == "state":
        print(json.dumps(workflow.accumulator.state, indent=2, sort_keys=True))
        return

    if args.command == "ask":
        if workflow.llm_adapter is None:
            parser.error("ask requires --llm-url, AAIS_BASE_URL, NOVA_BASE_URL, or SKILLZMCGEE_LLM_URL")
        if not args.prompt:
            parser.error("ask requires --prompt")
        print(workflow.llm_adapter.ask(args.prompt, context_slice=args.context_slice))
        return

    receipt = workflow.run_slice("slice_custom", {"message": "SkillzMcGee ready"}, echo_slice)
    print(receipt["output"]["message"])
