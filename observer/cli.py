"""Mission #002 Observer Kit — CLI and verification helpers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from constitutional.runtime import ConstitutionalStateRuntime, ObserverVerificationEngine, StateObject
from constitutional.runtime.receipts_v2 import TransitionReceiptV2
from receipts.models import from_transition_receipt_v2

_LOADED_PACKET: Path | None = None
_LOADED_CSR: ConstitutionalStateRuntime | None = None


def _default_csrs() -> list[tuple[str, ConstitutionalStateRuntime]]:
    runtimes: list[tuple[str, ConstitutionalStateRuntime]] = []
    try:
        from operator_kernel.csr import CSR as OP_CSR

        runtimes.append(("operator", OP_CSR))
    except Exception:
        pass
    try:
        from src.ugr.state_runtime import CSR as URG_CSR

        runtimes.append(("urg", URG_CSR))
    except Exception:
        pass
    try:
        from src.aaes_os.csr_bridge import get_aais_csr

        runtimes.append(("aais", get_aais_csr()))
    except Exception:
        pass
    if not runtimes:
        runtimes.append(("local", ConstitutionalStateRuntime()))
    return runtimes


def _all_states() -> list[tuple[str, StateObject]]:
    states: list[tuple[str, StateObject]] = []
    for runtime_name, csr in _default_csrs():
        for state_id, state in csr._states.items():  # noqa: SLF001 — observer introspection
            states.append((f"{runtime_name}:{state_id}", state))
    return states


def cmd_list_states(_args: argparse.Namespace) -> int:
    rows = _all_states()
    if not rows:
        print("No constitutional states registered.")
        return 0
    for key, state in rows:
        print(f"{key}\t{state.state_type}\t{state.current_state}")
    return 0


def _resolve_csr_for_state(state_id: str) -> tuple[ConstitutionalStateRuntime, str]:
    global _LOADED_CSR
    if _LOADED_CSR is not None:
        return _LOADED_CSR, state_id
    for _name, csr in _default_csrs():
        try:
            csr.get_state(state_id)
            return csr, state_id
        except KeyError:
            continue
    raise KeyError(f"state not found: {state_id}")


def cmd_show_state(args: argparse.Namespace) -> int:
    csr, state_id = _resolve_csr_for_state(args.state_id)
    state = csr.get_state(state_id)
    receipts = csr.receipts_for(state_id)
    replay = csr.replay(state_id)
    simplified = [from_transition_receipt_v2(r).model_dump() for r in receipts]
    out = {
        "state": json.loads(state.model_dump_json()),
        "receipts": simplified,
        "replay": json.loads(replay.model_dump_json()),
    }
    print(json.dumps(out, indent=2, default=str))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    csr, state_id = _resolve_csr_for_state(args.state_id)
    observer = ObserverVerificationEngine(csr)
    report = observer.verify_state(state_id)
    verdict = {
        "state_id": state_id,
        "state_reconstructed": not report.verification.divergence_detected,
        "state_replayed": not report.verification.divergence_detected,
        "divergence_detected": report.verification.divergence_detected,
        "remediation_valid": report.verification.remediation_valid,
        "amendments_valid": report.verification.amendments_valid,
        "failures": [f.model_dump() for f in report.failures],
    }
    print(json.dumps(verdict, indent=2, default=str))
    return 0 if not verdict["divergence_detected"] and not verdict["failures"] else 1


def load_packet(packet_dir: Path) -> ConstitutionalStateRuntime:
    """Load observer packet into an isolated CSR for offline verification."""
    global _LOADED_PACKET, _LOADED_CSR
    index_path = packet_dir / "packet_index.json"
    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        state_rel = index["paths"]["state"]
        receipts_rel = index["paths"]["receipts"]
        state_id = index["state_id"]
    else:
        state_rel = "state.json"
        receipts_rel = "receipts.json"
        state_id = json.loads((packet_dir / state_rel).read_text(encoding="utf-8"))["state_id"]

    csr = ConstitutionalStateRuntime()
    canonical = StateObject.model_validate(json.loads((packet_dir / state_rel).read_text(encoding="utf-8")))
    seed = canonical.model_copy(deep=True)
    seed.current_state = "Proposed"
    seed.history = []
    seed.version = 0
    csr.register_state(seed)

    receipts_path = packet_dir / receipts_rel
    if receipts_path.is_file():
        if receipts_path.suffix == ".jsonl":
            lines = receipts_path.read_text(encoding="utf-8").splitlines()
            receipts = [TransitionReceiptV2.model_validate(json.loads(line)) for line in lines if line.strip()]
        else:
            raw = json.loads(receipts_path.read_text(encoding="utf-8"))
            receipts = [TransitionReceiptV2.model_validate(r) for r in raw]
        accountable = canonical.accountability_chain[0] if canonical.accountability_chain else "observer-load"
        for receipt in receipts:
            csr.apply_transition(state_id, receipt, accountable_party=accountable)

    _LOADED_PACKET = packet_dir
    _LOADED_CSR = csr
    return csr


def cmd_load_packet(args: argparse.Namespace) -> int:
    packet_dir = Path(args.packet_dir).resolve()
    if not packet_dir.is_dir():
        print(f"Not a directory: {packet_dir}", file=sys.stderr)
        return 1
    csr = load_packet(packet_dir)
    print(json.dumps({"loaded": str(packet_dir), "states": list(csr._states.keys())}, indent=2))  # noqa: SLF001
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="observer", description="Mission #002 Observer Kit")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-states", help="List registered StateObject ids and current_state")

    show = sub.add_parser("show-state", help="Dump StateObject, receipts, and replay")
    show.add_argument("state_id")

    verify = sub.add_parser("verify", help="Run ObserverVerificationEngine on a state")
    verify.add_argument("state_id")

    load = sub.add_parser("load-packet", help="Load an observer packet directory")
    load.add_argument("packet_dir")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "list-states": cmd_list_states,
        "show-state": cmd_show_state,
        "verify": cmd_verify,
        "load-packet": cmd_load_packet,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
