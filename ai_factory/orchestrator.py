"""AI Factory orchestrator — runs stations in order."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_factory.binding import run_binding_station
from ai_factory.common import DEFAULT_LEDGER_PATH, DEFAULT_RUNTIME_ROOT, write_json
from ai_factory.envelope import revoke_build_receipt, run_envelope_station
from ai_factory.ledger import append_ledger_entry, find_ledger_entry, read_ledger
from ai_factory.proof_station import ProofStationError, run_proof_station
from ai_factory.runtime_bundle import run_runtime_station
from ai_factory.spec import AIBuildSpec, SpecStationError, load_build_spec, run_spec_station
from ai_factory.spine_profile import run_spine_station
from src.datetime_compat import UTC


@dataclass(slots=True)
class BuildResult:
    build_id: str
    output_dir: Path
    spec: AIBuildSpec
    spine_profile: dict[str, Any]
    cortex_bundle: dict[str, Any]
    bound_capability: dict[str, Any]
    proof_manifest: dict[str, Any]
    receipt: dict[str, Any]
    station_receipts: dict[str, dict[str, Any]] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)


class FactoryBuildError(RuntimeError):
    """Raised when any station fails."""


def build_output_dir(build_id: str, *, runtime_root: Path | None = None) -> Path:
    root = (runtime_root or DEFAULT_RUNTIME_ROOT).expanduser().resolve()
    return root / build_id


def run_build(
    *,
    spec_path: str | Path,
    repo_root: Path | None = None,
    runtime_root: Path | None = None,
    skip_pytest: bool = False,
    fixed_timestamp: str | None = None,
    ledger_path: Path | None = None,
) -> BuildResult:
    repo = (repo_root or Path(".")).resolve()
    generated_at = fixed_timestamp or datetime.now(UTC).isoformat()
    trace: list[str] = []
    station_receipts: dict[str, dict[str, Any]] = {}

    preview: AIBuildSpec
    try:
        preview = load_build_spec(spec_path)
    except SpecStationError as exc:
        raise FactoryBuildError(str(exc)) from exc
    output_dir = build_output_dir(preview.build_id, runtime_root=runtime_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    spec, spec_receipt = run_spec_station(spec_path=spec_path, output_dir=output_dir)
    station_receipts["spec"] = spec_receipt
    trace.extend(spec_receipt.get("trace") or [])

    spine_profile, spine_receipt = run_spine_station(spec=spec, output_dir=output_dir)
    station_receipts["spine"] = spine_receipt
    trace.extend(spine_receipt.get("trace") or [])

    cortex_bundle, runtime_receipt = run_runtime_station(
        spec=spec,
        spine_profile=spine_profile,
        output_dir=output_dir,
        repo_root=repo,
    )
    station_receipts["runtime"] = runtime_receipt
    trace.extend(runtime_receipt.get("trace") or [])

    bound_capability, binding_receipt = run_binding_station(spec=spec, output_dir=output_dir)
    station_receipts["binding"] = binding_receipt
    trace.extend(binding_receipt.get("trace") or [])

    try:
        proof_manifest, proof_receipt = run_proof_station(
            spec=spec,
            output_dir=output_dir,
            repo_root=repo,
            skip_pytest=skip_pytest,
            generated_at_utc=generated_at,
        )
    except ProofStationError as exc:
        raise FactoryBuildError(str(exc)) from exc
    station_receipts["proof"] = proof_receipt
    trace.extend(proof_receipt.get("trace") or [])

    receipt, envelope_receipt = run_envelope_station(
        spec=spec,
        spine_profile=spine_profile,
        proof_manifest=proof_manifest,
        output_dir=output_dir,
        station_receipts=station_receipts,
        generated_at_utc=generated_at,
    )
    station_receipts["envelope"] = envelope_receipt
    trace.extend(envelope_receipt.get("trace") or [])

    ledger_entry = append_ledger_entry(
        {
            "event": "build_complete",
            "build_id": spec.build_id,
            "generated_at_utc": generated_at,
            "claim_label": receipt.get("claim_label"),
            "risk_rating": spec.risk_level,
            "output_dir": str(output_dir.resolve()),
            "receipt_path": str((output_dir / "AI_BUILD_RECEIPT.json").resolve()),
            "lifecycle_status": receipt.get("lifecycle_status"),
        },
        ledger_path=ledger_path,
    )
    trace.append("append_ledger_entry")

    return BuildResult(
        build_id=spec.build_id,
        output_dir=output_dir,
        spec=spec,
        spine_profile=spine_profile,
        cortex_bundle=cortex_bundle,
        bound_capability=bound_capability,
        proof_manifest=proof_manifest,
        receipt=receipt,
        station_receipts=station_receipts,
        trace=trace,
    )


def deploy_active_build(
    *,
    build_id: str,
    runtime_root: Path | None = None,
    repo_root: Path | None = None,
) -> Path:
    del repo_root
    root = (runtime_root or DEFAULT_RUNTIME_ROOT).expanduser().resolve()
    source = root / build_id
    if not source.is_dir():
        raise FactoryBuildError(f"build output not found: {source}")

    receipt_path = source / "AI_BUILD_RECEIPT.json"
    if receipt_path.is_file():
        import json

        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if str(receipt.get("lifecycle_status") or "") == "revoked":
            raise FactoryBuildError(f"build revoked: {build_id}")
        proof_path = source / "proof_manifest.json"
        if proof_path.is_file():
            proof = json.loads(proof_path.read_text(encoding="utf-8"))
            if proof.get("deploy_blocked"):
                raise FactoryBuildError("proof manifest blocks deploy")

    active_dir = root / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    pointer = active_dir / "build_id.txt"
    pointer.write_text(build_id + "\n", encoding="utf-8")
    write_json(
        active_dir / "active_pointer.json",
        {
            "build_id": build_id,
            "source_dir": str(source.resolve()),
            "receipt_path": str((source / "AI_BUILD_RECEIPT.json").resolve()),
        },
    )

    return pointer


def build_status(
    *,
    build_id: str | None = None,
    ledger_path: Path | None = None,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    root = (runtime_root or DEFAULT_RUNTIME_ROOT).expanduser().resolve()
    if build_id:
        entry = find_ledger_entry(build_id, ledger_path=ledger_path)
        receipt_path = root / build_id / "AI_BUILD_RECEIPT.json"
        receipt = None
        if receipt_path.is_file():
            import json

            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        return {
            "build_id": build_id,
            "ledger_entry": entry,
            "receipt": receipt,
            "output_dir": str((root / build_id).resolve()),
        }
    return {
        "ledger_entries": read_ledger(ledger_path=ledger_path),
        "active_build_id": (
            (root / "active" / "build_id.txt").read_text(encoding="utf-8").strip()
            if (root / "active" / "build_id.txt").is_file()
            else None
        ),
    }


def revoke_build(
    *,
    build_id: str,
    runtime_root: Path | None = None,
    ledger_path: Path | None = None,
) -> dict[str, Any]:
    root = (runtime_root or DEFAULT_RUNTIME_ROOT).expanduser().resolve()
    output_dir = root / build_id
    receipt = revoke_build_receipt(output_dir)
    entry = append_ledger_entry(
        {
            "event": "build_revoked",
            "build_id": build_id,
            "lifecycle_status": "revoked",
            "receipt_path": str((output_dir / "AI_BUILD_RECEIPT.json").resolve()),
        },
        ledger_path=ledger_path or DEFAULT_LEDGER_PATH,
    )
    return {"receipt": receipt, "ledger_entry": entry}
