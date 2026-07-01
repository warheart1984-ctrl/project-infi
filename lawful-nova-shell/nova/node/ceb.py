from __future__ import annotations

import hashlib
import json
import shutil
import time
import zipfile
from pathlib import Path
from typing import Any

from nova.node.conformance import generate_n0_report
from nova.node.continuity import continuity_log_path
from nova.node.identity import NodeIdentity
from nova.node.ledger import governance_ledger_path, read_ledger, runtime_dir, stable_json
from nova.node.policy import GovernanceRuntime


def generate_evidence_bundle(output_dir: str | Path, *, report: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(output_dir)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    report = report or generate_n0_report()
    identity = NodeIdentity.load("./policy.yaml")
    policy = GovernanceRuntime().policy

    _write_json(root / "identity" / "identity.json", {
        "node_id": identity.node_id,
        "operator_id": identity.operator_id,
        "policy_hash": identity.policy_hash,
        "public_key": None,
    })
    _write_text(root / "policy" / "policy.yaml", Path("./policy.yaml").read_text(encoding="utf-8") if Path("./policy.yaml").exists() else stable_json(policy))
    _write_text(root / "policy" / "policy_hash.txt", identity.policy_hash + "\n")
    _write_text(root / "policy" / "policy_version.txt", str(policy.get("version", "1.0")) + "\n")

    continuity_path = continuity_log_path()
    _write_text(
        root / "continuity" / "continuity.log",
        continuity_path.read_text(encoding="utf-8") if continuity_path.exists() else "",
    )
    _write_text(root / "continuity" / "continuity_hash.txt", _file_hash(root / "continuity" / "continuity.log") + "\n")

    for entry in read_ledger():
        target = "federation/gossip.jsonl" if entry.get("entry_type") == "nodeGossipReceipt" else "federation/handshake.jsonl"
        _append_text(root / target, stable_json(entry) + "\n")
    _write_json(root / "federation" / "trust_levels.json", _trust_levels())

    receipts_dir = root / "receipts"
    receipts_dir.mkdir(parents=True, exist_ok=True)
    for result_path in (runtime_dir() / "results").glob("*.json"):
        target = receipts_dir / result_path.name
        target.write_text(result_path.read_text(encoding="utf-8"), encoding="utf-8")

    _write_json(root / "conformance" / "n0_report.json", report)
    _write_text(root / "conformance" / "n0_report_hash.txt", _file_hash(root / "conformance" / "n0_report.json") + "\n")
    for folder in ["replay/original", "replay/replayed", "replay/diff", "mesh"]:
        (root / folder).mkdir(parents=True, exist_ok=True)

    files = [
        {"path": str(path.relative_to(root)).replace("\\", "/"), "sha256": _file_hash(path)}
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]
    manifest = {
        "version": "CEB-1.0",
        "node_id": identity.node_id,
        "operator_id": identity.operator_id,
        "policy_hash": identity.policy_hash,
        "generated_on": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files": files,
    }
    _write_json(root / "manifest.json", manifest)
    bundle_path = root.with_suffix(".zip")
    _zip_dir(root, bundle_path)
    manifest["bundle_hash"] = _file_hash(bundle_path)
    _write_json(root / "manifest.json", manifest)
    _zip_dir(root, bundle_path)
    return {
        "bundle_path": str(bundle_path),
        "manifest_path": str(root / "manifest.json"),
        "manifest": manifest,
    }


def _write_json(path: Path, data: Any) -> None:
    _write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _append_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _zip_dir(root: Path, bundle_path: Path) -> None:
    if bundle_path.exists():
        bundle_path.unlink()
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(root))


def _trust_levels() -> dict[str, str]:
    levels: dict[str, str] = {}
    for entry in read_ledger():
        summary = entry.get("summary") or {}
        node_id = summary.get("node_id")
        if node_id:
            levels[str(node_id)] = str(entry.get("trust_level") or "limited")
    return levels
