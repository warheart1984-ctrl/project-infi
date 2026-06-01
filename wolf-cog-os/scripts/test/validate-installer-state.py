#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Validate CoGOS installer state.json")
    parser.add_argument("--state", required=True, help="Path to state.json")
    parser.add_argument("--require-proof", action="store_true", help="Require install_proof.json in target root")
    parser.add_argument("--target-root", default="", help="Target root path used by installer apply")
    args = parser.parse_args()

    state_path = Path(args.state)
    if not state_path.exists():
        raise SystemExit(f"state.json not found: {state_path}")

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    steps = payload.get("steps", [])
    failures = [s for s in steps if s.get("status") == "failed"]
    incomplete = [s for s in steps if s.get("status") not in ("completed", "pending")]

    if failures:
        names = ", ".join(s.get("name", "unknown") for s in failures)
        raise SystemExit(f"Installer failed steps detected: {names}")

    if incomplete:
        names = ", ".join(f"{s.get('name','unknown')}={s.get('status')}" for s in incomplete)
        raise SystemExit(f"Installer has non-terminal steps: {names}")

    if args.require_proof:
        if not args.target_root:
            raise SystemExit("--target-root is required with --require-proof")
        target_proof = Path(args.target_root) / "opt/cogos/memory/logs/install_proof.json"
        state_proof = state_path.parent / "install_proof.json"
        proof_candidates = [target_proof, state_proof]
        if not any(candidate.exists() for candidate in proof_candidates):
            print(f"[validate-installer-state] expected proof path: {target_proof}")
            print(f"[validate-installer-state] expected fallback proof path: {state_proof}")
            raise SystemExit(f"install_proof.json missing: {target_proof} (fallback: {state_proof})")

    print("Installer state validation OK.")


if __name__ == "__main__":
    main()
