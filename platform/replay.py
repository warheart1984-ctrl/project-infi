"""Cross-machine replay runner (v1 + v2 + v3)."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from platform.common import write_json
from platform.proof.signing import sign_attestation


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_commands(commands: Any) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if isinstance(commands, dict):
        for name, cmd in commands.items():
            completed = subprocess.run(str(cmd), shell=True, capture_output=True, text=True, check=False)
            results.append(
                {
                    "name": name,
                    "command": cmd,
                    "exit_code": completed.returncode,
                    "stdout_tail": (completed.stdout or "")[-500:],
                    "stderr_tail": (completed.stderr or "")[-500:],
                }
            )
            if completed.returncode != 0:
                break
        return results
    for cmd in commands or []:
        completed = subprocess.run(str(cmd), shell=True, capture_output=True, text=True, check=False)
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


def run_replay(*, manifest_path: str | Path) -> int:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("operational_status") == "inactive":
        print("replay manifest inactive", file=sys.stderr)
        return 2

    version = str(manifest.get("manifest_version") or "")
    runner_reports: list[dict[str, Any]] = []

    is_v3 = "v3" in version
    if (version.endswith("v2") or is_v3) and manifest.get("runners"):
        for runner in manifest.get("runners") or []:
            rid = str(runner.get("runner_id") or "runner")
            cmds = runner.get("commands") or {}
            results = _run_commands(cmds)
            failed = any(r.get("exit_code", 0) != 0 for r in results)
            digest = hashlib.sha256(json.dumps(results, sort_keys=True).encode()).hexdigest()
            runner_reports.append(
                {
                    "runner_id": rid,
                    "region": runner.get("region"),
                    "command_results": results,
                    "result_hash": digest,
                    "post_attestation_url": runner.get("post_attestation_url"),
                    "claim_label": "rejected" if failed else "asserted",
                }
            )
        hashes = {r["result_hash"] for r in runner_reports if r.get("result_hash")}
        claim = "proven" if len(hashes) == 1 and runner_reports else "asserted"
        if len(hashes) > 1:
            claim = "rejected"
        report = {
            "report_version": "platform.platform_replay_report.v3" if is_v3 else "platform.platform_replay_report.v2",
            "manifest_version": version,
            "runner_reports": runner_reports,
            "result_hash": next(iter(hashes)) if len(hashes) == 1 else "",
            "claim_label": claim,
        }
    else:
        report = {
            "report_version": "platform.platform_replay_report.v1",
            "manifest_version": version,
            "subsystem": manifest.get("subsystem", "platform"),
            "command_results": _run_commands(manifest.get("commands") or []),
            "artifact_hashes": {},
            "claim_label": "asserted",
        }
        if any(r.get("exit_code", 0) != 0 for r in report["command_results"]):
            report["claim_label"] = "rejected"
        for name, rel in (manifest.get("artifact_hashes") or {}).items():
            path = Path(str(rel))
            if path.is_file():
                report["artifact_hashes"][name] = _sha256_file(path)

    if is_v3:
        out_name = "platform_replay_report.v3.json"
    elif version.endswith("v2"):
        out_name = "platform_replay_report.v2.json"
    else:
        out_name = "platform_replay_report.v1.json"
    out = Path(".runtime/platform/replay") / out_name
    write_json(out, report)
    print(json.dumps({"status": "ok", "report": str(out), "claim_label": report["claim_label"]}))
    return 0 if report["claim_label"] not in {"rejected"} else 1


def post_replay_attestations(
    *,
    report: dict[str, Any],
    job_id: str,
    base_url: str,
    api_key: str,
) -> list[dict[str, Any]]:
    """POST attestations from replay runner reports (CI v28/v36)."""
    results: list[dict[str, Any]] = []
    for rr in report.get("runner_reports") or []:
        url = str(rr.get("post_attestation_url") or "").strip()
        if not url:
            url = f"{base_url.rstrip('/')}/v1/jobs/{job_id}/attestations"
        h = str(rr.get("result_hash") or "")
        rid = str(rr.get("runner_id") or "runner")
        sig, _alg = sign_attestation(job_id=job_id, runner_id=rid, result_hash=h)
        body = json.dumps(
            {
                "runner_id": rid,
                "result_hash": h,
                "region": rr.get("region") or "us",
                "signature": sig,
            }
        ).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "X-Api-Key": api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                results.append({"runner_id": rid, "status": resp.status})
        except urllib.error.URLError as exc:
            results.append({"runner_id": rid, "error": str(exc)})
    return results
