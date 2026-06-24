"""D-3 Seal wire objects and Mission #003 reproduction packet."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.crk1.mission_003_packet import (
    EXTERNAL_REPRODUCTION_PACKET,
    SUPPORTING_ARTIFACTS,
    compute_packet_fingerprint,
    verify_packet_artifacts,
)


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class ReproductionSeal(BaseModel):
    """D-3 Seal — founder-independent reproduction attestation (wire object)."""

    id: str
    type: Literal["ReproductionSeal"] = "ReproductionSeal"
    created_at: str = Field(default_factory=_now_iso)
    created_by: str
    epoch: int
    payload: dict[str, Any]
    links: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_d3_certificate(
        cls,
        *,
        seal_id: str,
        created_by: str,
        epoch: int,
        runtime_rebuilt: bool,
        oral_tradition_used: bool,
        tests_executed: dict[str, str],
        all_passed: bool,
        notes: str = "",
        reproduction_packet_id: str,
        test_harness_ids: list[str],
        external_steward_id: str,
        governance_receipt_ids: list[str] | None = None,
    ) -> "ReproductionSeal":
        return cls(
            id=seal_id,
            created_by=created_by,
            epoch=epoch,
            payload={
                "runtime_rebuilt": runtime_rebuilt,
                "source_of_truth": reproduction_packet_id,
                "oral_tradition_used": oral_tradition_used,
                "tests_executed": tests_executed,
                "results": {
                    "all_passed": all_passed,
                    **({"notes": notes} if notes else {}),
                },
            },
            links={
                "reproduction_packet_id": reproduction_packet_id,
                "test_harness_ids": test_harness_ids,
                "external_steward_id": external_steward_id,
                **(
                    {"governance_receipt_ids": governance_receipt_ids}
                    if governance_receipt_ids
                    else {}
                ),
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class ReproductionPacket(BaseModel):
    """Mission #003 external reproduction packet manifest."""

    id: str = "RP-CRK1-v1.0"
    type: Literal["ReproductionPacket"] = "ReproductionPacket"
    created_at: str = Field(default_factory=_now_iso)
    created_by: str = "Founders"
    epoch: int = 1
    payload: dict[str, Any] = Field(default_factory=dict)
    links: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def build(
        cls,
        *,
        kernel_id: str = "KERNEL-3",
        epoch: int = 3,
        test_suite_ids: list[str] | None = None,
    ) -> "ReproductionPacket":
        ok, missing = verify_packet_artifacts()
        fingerprint = compute_packet_fingerprint()
        spec_docs = [artifact.name for artifact in EXTERNAL_REPRODUCTION_PACKET[:3]]
        reference_impl = [str(artifact.path.name) for artifact in EXTERNAL_REPRODUCTION_PACKET[3:6]]
        test_harness = [
            "tests/crk1/test_crk1_redteam_suite.py",
            "tests/crk1/test_mission_004_005.py",
            "tests/crk1/test_crk1_wire_v01.py",
            "src/crk1/semantic_reproduction_harness.py",
            "src/crk1/external_reproduction_harness.py",
        ]
        return cls(
            epoch=epoch,
            payload={
                "version": "CRK-1 v1.0",
                "packet_fingerprint": fingerprint,
                "artifacts_verified": ok,
                "missing_artifacts": missing,
                "contents": {
                    "spec_docs": spec_docs,
                    "reference_implementation": reference_impl,
                    "test_harness": test_harness,
                    "reproduction_instructions": [
                        "Clone repository and install Python 3.12+ dependencies",
                        "Run pytest tests/crk1/ — all suites must pass",
                        "Verify packet fingerprint matches payload.packet_fingerprint",
                        "Issue ReproductionSeal with oral_tradition_used=false",
                    ],
                },
            },
            links={
                "kernel_id": kernel_id,
                "test_suite_ids": test_suite_ids
                or ["TH-0001", "TH-0002", "TH-0003"],
            },
        )

    def packet_hash(self) -> str:
        payload = self.model_dump(mode="json")
        payload.pop("created_at", None)
        encoded = json.dumps(payload, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        data["packet_hash"] = self.packet_hash()
        return data
