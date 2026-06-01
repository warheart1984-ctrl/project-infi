"""UGR trust bundle organ — cross-profile proof orchestration."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from src.ugr.trust_bundle.evidence import (
    BUNDLE_ID,
    ORGAN_VERSION,
    MachineProfile,
    ScenarioEvidence,
    machine_profile,
    utc_now_iso,
    write_proof_bundle,
)
from src.ugr.trust_bundle.scenarios import SCENARIO_RUNNERS


DEFAULT_SCENARIOS = ("mesh_parity", "causal_rebuild", "llm_execution_smoke", "gate_manifest")
CROSS_PROFILE_IDS = ("machine-a", "machine-b")


class TrustBundleOrgan:
    """Run UGR proof scenarios across isolated runtime profiles and emit a proof bundle."""

    def __init__(
        self,
        *,
        output_dir: str | Path | None = None,
        scenarios: tuple[str, ...] = DEFAULT_SCENARIOS,
        machine_ids: tuple[str, ...] = CROSS_PROFILE_IDS,
    ):
        self.output_dir = Path(output_dir or Path(".runtime") / "trust-bundles" / "latest")
        self.scenarios = scenarios
        self.machine_ids = machine_ids

    def run(self) -> dict[str, Any]:
        machine_results: dict[str, dict[str, Any]] = {}
        scenario_records: list[dict[str, Any]] = []
        parity: dict[str, Any] = {}

        with tempfile.TemporaryDirectory(prefix="ugr-trust-organ-") as temp_base:
            base = Path(temp_base)
            profiles: dict[str, MachineProfile] = {}
            payload_hashes: dict[str, dict[str, str]] = {scenario: {} for scenario in self.scenarios}

            for machine_id in self.machine_ids:
                runtime_root = base / machine_id
                runtime_root.mkdir(parents=True, exist_ok=True)
                profiles[machine_id] = machine_profile(machine_id, runtime_root)
                machine_results[machine_id] = {"scenarios": {}}

                for scenario_id in self.scenarios:
                    runner = SCENARIO_RUNNERS[scenario_id]
                    evidence = runner(machine_id=machine_id, runtime_root=runtime_root)
                    scenario_records.append(evidence.to_dict())
                    machine_results[machine_id]["scenarios"][scenario_id] = evidence.to_dict()
                    if evidence.payload_sha256:
                        payload_hashes[scenario_id][machine_id] = evidence.payload_sha256

            for scenario_id, hashes in payload_hashes.items():
                if len(hashes) < 2:
                    continue
                if scenario_id == "gate_manifest":
                    continue
                values = list(hashes.values())
                parity[scenario_id] = {
                    "matched": len(set(values)) == 1,
                    "machine_hashes": hashes,
                }

        failures = [record for record in scenario_records if record.get("status") != "pass"]
        cross_profile_ok = all(item.get("matched") for item in parity.values()) if parity else True
        overall_status = "pass" if not failures and cross_profile_ok else "fail"

        bundle = {
            "bundle_id": BUNDLE_ID,
            "organ_version": ORGAN_VERSION,
            "generated_at_utc": utc_now_iso(),
            "overall_status": overall_status,
            "machines": {machine_id: profile.to_dict() for machine_id, profile in profiles.items()},
            "machine_results": machine_results,
            "cross_profile_parity": parity,
            "scenario_records": scenario_records,
            "verification_command": "make ugr-trust-bundle-gate",
        }
        proof_path = write_proof_bundle(self.output_dir, bundle)
        bundle["proof_bundle_path"] = str(proof_path)
        bundle["proof_bundle_sha256_path"] = str(self.output_dir / "proof_bundle.sha256")
        return bundle

    def receive_claim(self, claim: dict[str, Any], *, bridge_trace: dict[str, Any] | None = None) -> dict[str, Any]:
        """Ledger bridge destination — validate receipt only (no external apply)."""
        import hashlib
        import json
        import uuid

        cid = str(claim.get("claim_id") or uuid.uuid4())
        body = json.dumps({"claim_id": cid, "law_id": claim.get("law_id")}, sort_keys=True)
        receipt_id = str(uuid.uuid4())
        return {
            "receipt_id": receipt_id,
            "claim_id": cid,
            "acknowledged": True,
            "claim_label": "proven",
            "bridge_trace_id": (bridge_trace or {}).get("trace_id"),
            "artifact_sha256": hashlib.sha256(body.encode()).hexdigest(),
            "claim_label_doctrine": "asserted",
        }
