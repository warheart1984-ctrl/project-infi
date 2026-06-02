"""Lab cross-machine replay runner (INV-9)."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from lab.common import json_stable, sha256_file, write_json


def _run_commands(commands: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for cmd in commands:
        completed = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
        results.append(
            {
                "command": cmd,
                "exit_code": completed.returncode,
                "stdout_tail": (completed.stdout or "")[-500:],
                "stderr_tail": (completed.stderr or "")[-500:],
            }
        )
        if completed.returncode != 0:
            break
    return results


def run_lab_replay(*, manifest_path: Path, repo_root: Path | None = None) -> dict[str, Any]:
    """Execute lab replay commands from manifest and emit report."""
    root = repo_root or Path.cwd()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    commands = list(manifest.get("commands") or [])
    if not commands:
        commands = [
            "python -m pytest tests/test_lab_http.py tests/test_lab_worktree.py -q",
        ]

    results = _run_commands(commands)
    report_dir = root / ".runtime" / "lab" / "replay"
    report_dir.mkdir(parents=True, exist_ok=True)

    receipt_path = manifest.get("session_receipt_path")
    receipt_hash = ""
    if receipt_path:
        path = Path(str(receipt_path))
        if not path.is_absolute():
            path = root / path
        if path.is_file():
            receipt_hash = sha256_file(path)

    report = {
        "manifest_version": manifest.get("manifest_version", "lab.cross_machine.v1"),
        "debt_register_id": manifest.get("debt_register_id", "INV-9"),
        "operational_status": manifest.get("operational_status", "inactive"),
        "command_results": results,
        "session_receipt_hash": receipt_hash,
        "passed": all(item.get("exit_code") == 0 for item in results),
        "claim_label": "asserted",
    }
    report["result_hash"] = hashlib.sha256(json_stable(report).encode("utf-8")).hexdigest()
    out_path = report_dir / "lab_replay_report.json"
    write_json(out_path, report)
    return report


def main(argv: list[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    manifest = Path(args[0] if args else "docs/proof/lab/cross_machine/REPLAY_MANIFEST.json")
    if not manifest.is_file():
        print(f"[lab-replay] manifest missing: {manifest}", file=sys.stderr)
        return 2
    report = run_lab_replay(manifest_path=manifest)
    print(json.dumps(report, indent=2))
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
