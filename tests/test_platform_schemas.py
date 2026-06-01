"""Validate platform JSON schema examples."""

from __future__ import annotations

import json
from pathlib import Path


SCHEMA_DIR = Path(__file__).resolve().parents[1] / "platform" / "schemas"


def test_platform_job_schema_example() -> None:
    example = {
        "job_version": "platform.platform_job.v1",
        "job_id": "job-demo",
        "org_id": "acme",
        "correlation_id": "corr-demo",
        "subsystem": "mechanic",
        "subsystem_job_id": "case-demo",
        "kind": "mechanic.scan",
        "status": "queued",
        "claim_label": "asserted",
        "created_at": "2026-05-31T12:00:00+00:00",
        "updated_at": "2026-05-31T12:00:00+00:00",
        "actor_principal_id": "principal-acme",
        "links": [],
        "metadata": {},
    }
    schema = json.loads((SCHEMA_DIR / "platform_job.v1.json").read_text(encoding="utf-8"))
    assert schema["properties"]["job_version"]["const"] == example["job_version"]


def test_platform_artifact_ref_schema_example() -> None:
    example = {
        "ref_version": "platform.platform_artifact_ref.v1",
        "ref_id": "art-demo",
        "org_id": "acme",
        "subsystem": "mechanic",
        "logical_path": "mechanic_scan.v1.json",
        "storage_uri": "file:///tmp/x.json",
        "sha256": "a" * 64,
        "claim_label": "asserted",
        "lineage_parent_refs": [],
        "acl": {"org_id": "acme", "visibility": "org_private"},
        "registered_at": "2026-05-31T12:00:00+00:00",
    }
    schema = json.loads((SCHEMA_DIR / "platform_artifact_ref.v1.json").read_text(encoding="utf-8"))
    assert schema["properties"]["ref_version"]["const"] == example["ref_version"]


def test_platform_identity_schema_example() -> None:
    example = {
        "identity_version": "platform.platform_identity.v1",
        "org_id": "acme",
        "principal_id": "principal-acme",
        "roles": ["operator"],
    }
    schema = json.loads((SCHEMA_DIR / "platform_identity.v1.json").read_text(encoding="utf-8"))
    assert "platform_admin" in schema["properties"]["roles"]["items"]["enum"]


def test_mesh_schemas_present() -> None:
    for name in (
        "operator_presence.v1.json",
        "job_assignment.v1.json",
        "mesh_event.v1.json",
        "handoff_bundle.v1.json",
    ):
        schema = json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
        assert schema.get("type") == "object"


def test_workflow_listing_v2_fields() -> None:
    schema = json.loads((SCHEMA_DIR / "workflow_listing.v1.json").read_text(encoding="utf-8"))
    props = schema.get("properties") or {}
    assert "approval_status" in props
    assert "steps" in props


def test_proof_attestation_signature_field() -> None:
    schema = json.loads((SCHEMA_DIR / "proof_attestation.v1.json").read_text(encoding="utf-8"))
    props = schema.get("properties") or {}
    assert "signature" in props
    assert "signature_alg" in props


def test_webhook_and_bundle_schemas() -> None:
    wh = json.loads((SCHEMA_DIR / "webhook_subscription.v1.json").read_text(encoding="utf-8"))
    assert wh["properties"]["subscription_version"]["const"] == "platform.webhook_subscription.v1"
    bundle = json.loads((SCHEMA_DIR / "proof_attestation_bundle.v1.json").read_text(encoding="utf-8"))
    assert bundle["properties"]["bundle_version"]["const"] == "platform.proof_attestation_bundle.v1"
